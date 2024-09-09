from html.parser import HTMLParser
from pydantic import BaseModel
import json
from database import store_lesson_errors
from htmlescape import convert_to_html_escape

class SelectionItem(BaseModel):
    anchorOffset : int
    focusOffset : int
    editorDomString : str
    comment : str
    markType : str
    action: str

class MarkedLinesParser(HTMLParser):
    def analyze_lesson(self, lesson):
        self.sentences = []
        self.marked_lines = []
        self.marked_lines_numbers = {}
        self.current_line_number = 0
        self.feed(lesson)

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.current_sentence = ""
        elif tag == "mark":
            if not self.current_line_number in self.marked_lines_numbers:
                self.marked_lines_numbers[self.current_line_number] = True
            attrs_string = ""
            for attr_name, attr_value in attrs:
                print(f"attr_name : {attr_name}, attr_value : {attr_value}")
                escaped_attr_value = convert_to_html_escape(attr_value)
                attrs_string += f" {attr_name}='{escaped_attr_value}'"
                print(f"---- escaped_attr_value : {escaped_attr_value}")
                if attr_value:
                    for index, char in enumerate(attr_value):
                        print(f"attr_name = {attr_name}, char : {char}, {ord(char)}, {index}")
                else:
                     print(f"attr_name = {attr_name}")
            if attrs_string:
                self.current_sentence += f"<{tag}{attrs_string}>"
            else:
                self.current_sentence += f"<{tag}>"
        else:
            self.current_sentence += f"<{tag}>"
        

    def handle_endtag(self, tag):
        if tag == "p":
            self.sentences.append(self.current_sentence.strip())
            self.current_line_number += 1
        else:
            self.current_sentence += f"</{tag}>"

    def handle_data(self, data):
        if hasattr(self, "current_sentence"):
            self.current_sentence += data
    
    def get_marked_lines_numbers(self):
        return self.marked_lines_numbers

    def get_sentences(self):
        return self.sentences
    
    def handle_charref(name):
        print('In handle_charref for : ', name)
    
mark_parser = MarkedLinesParser(convert_charrefs = False)
    
def extract_selection(lesson):
    mark_parser.analyze_lesson(lesson)
    marked_lines_numbers = mark_parser.get_marked_lines_numbers()
    sentences = mark_parser.get_sentences()
    return marked_lines_numbers, sentences
    
def extract_paragraphs(lesson):
    mark_parser.analyze_lesson(lesson)
    return mark_parser.get_sentences()

def get_html_text_with_mark(element, anchorOffset, focusOffset, mark_tag_string, mark_open = False, open_tag = None):
    text = ''
    #print(f"tag : {element['tagName']}, status : {element['status']}") 
    if element['tagName']:
        if element['tagName'] == 'p':
            if mark_open:
                text += '<' + element['tagName'] + '>' + mark_tag_string
            else:
                text += '<' + element['tagName'] + '>'
        else:
            text += '<' + element['tagName']
            for name in element['attributes']:
                text += f" {name}='{convert_to_html_escape(element['attributes'][name])}'"
            text += '>'
        if element['status'] == 'isAnchor':
            text += element['textContent'][:anchorOffset]
            text += '</' + element['tagName'] + '>' + mark_tag_string + '<' + element['tagName'] + '>'
            text += element['textContent'][anchorOffset:]
            mark_open = True
        elif element['status'] == 'isAnchorAndFocus':
            text += element['textContent'][:anchorOffset]
            text += mark_tag_string
            text += element['textContent'][anchorOffset:focusOffset]
            text += '</mark>'
            text += element['textContent'][focusOffset:]
        elif element['status'] == 'isFocus':
            text += element['textContent'][:focusOffset]
            text += '</' + element['tagName'] + '>' + '</mark>' + '<' + element['tagName'] + '>'
            text += element['textContent'][focusOffset:]
            mark_open = False
        else:
            for child in element['children']:
                child_text, mark_open = get_html_text_with_mark(child, anchorOffset, focusOffset, mark_tag_string, mark_open, element['tagName'])
                text += child_text
        #print(f"tag : {element['tagName']}, mark_open : {mark_open}, {element['textContent']}")
        if element['tagName'] == 'p':
            if mark_open:
                text += '</mark></' + element['tagName'] + '>'
            else:
                text += '</' + element['tagName'] + '>'
        else:
            text += '</' + element['tagName'] + '>'
    else:  # element is element text
        if element['status'] == 'isAnchor':
            text += element['textContent'][:anchorOffset]
            if open_tag == 'b':
                text += '</b>' + mark_tag_string + '<b>'    
            else:
                text += mark_tag_string
            text += element['textContent'][anchorOffset:]
            mark_open = True
        elif element['status'] == 'isAnchorAndFocus':
            text += element['textContent'][:anchorOffset]
            text += mark_tag_string + element['textContent'][anchorOffset:focusOffset] + '</mark>'
            text += element['textContent'][focusOffset:]
        elif element['status'] == 'isFocus':
            text += element['textContent'][:focusOffset]
            if open_tag == 'b':
                text += '</b></mark><b>'    
            else:
                text += '</mark>'
            text += element['textContent'][focusOffset:]
            mark_open = False
        else:
            text += element['textContent']
        #print(f"tag : {element['tagName']}, mark_open : {mark_open}, {element['textContent']}")
    return text, mark_open
    
def get_html_with_selection(div_element, anchorOffset, focusOffset, mark_tag_string):
    text = ""
    mark_open = False
    for element in div_element['children']:
        txt, mark_open = get_html_text_with_mark(element, anchorOffset, focusOffset, mark_tag_string, mark_open)
        text += txt
    return text

def get_html_text(element):
    if element['tagName']:
        text = '<' + element['tagName']
        for name in element['attributes']:
            text += f" {name}='{convert_to_html_escape(element['attributes'][name])}'"
        text += '>'
        for child in element['children']:
            text += get_html_text(child)
        text += f"</{element['tagName']}>"
    else:
        text = element['textContent']
    return text
    


def delete_marked_selection(element):
    #print(element['tagName'])
    if element['status'] == 'isAnchor':
        print(f"Anchor found : {element}")
        return element
    elif element['status'] == 'isAnchorAndFocus':
        print(f"Anchor is Focus found : {element}")
        return element
    else:
        for index, child in enumerate(element['children']):
            print(child['tagName'])
            if child['tagName'] == 'mark':
                founded_selection_element = delete_marked_selection(child)
                if founded_selection_element:
                    element_children = element['children']
                    new_element_children_begining = element_children[:index]
                    new_element_children_end = element_children[index+1:]
                    new_element_children = new_element_children_begining
                    for mark_child in child['children']:
                        new_element_children.append(mark_child)
                    new_element_children += new_element_children_end
                    element['children'] = new_element_children
                    return founded_selection_element
            elif child['status'] == 'isAnchor':
                print(f"Anchor found : {child}")
                return child
            elif child['status'] == 'isAnchorAndFocus':
                print(f"Anchor is Focus found : {child}")
                return child
            else:
                founded_selection_element = delete_marked_selection(child)
                if founded_selection_element:
                    return founded_selection_element
    return None

def get_html_with_selected_mark_removed(div_element):
    delete_marked_selection(div_element)
    text = ""
    for element in div_element['children']:
        text += get_html_text(element)
    return text

def proceed_marked_selection(lesson_nb, item: SelectionItem): 
    print(f"------------ of length :{len(item.comment)}")
    print(f"------------ comment : {item.comment}")
    editor = json.loads(item.editorDomString)

    if (item.action == 'MARK' or item.action == 'STORE'):
        comment = convert_to_html_escape(item.comment)
        mark_tag_string = f"<mark class='{item.markType}'"
        if item.comment:
            mark_tag_string += f" title='{comment}'>"
        else:
            mark_tag_string += ">"

        print(f"+++++++++++ mark_tag_string : {mark_tag_string}")
        #print(f"************* json editor: {editor}")
        html_with_selection = get_html_with_selection(editor, item.anchorOffset, item.focusOffset, mark_tag_string)
        print(f"------------- In proceed_marked_selection {html_with_selection}")
        html_with_selection = html_with_selection.replace("\n", "")
        print(f"html_with_selection : {html_with_selection}")
        if item.action == 'STORE':
            print(f"---------- extract_selectionAction : {item.action}")
            marked_lines_numbers, sentences = extract_selection(html_with_selection)
            print(marked_lines_numbers)
            print(sentences)
            store_lesson_errors(lesson_nb, sentences, marked_lines_numbers)
        return html_with_selection
    elif item.action == 'CLEAR':
        print(f"-- item.action == MARK ")
        #print(f"************* json editor: {editor}")
        anchor = delete_marked_selection(editor)
        html_with_selection_removed = get_html_with_selected_mark_removed(editor)
        #html_with_selection_removed = get_html_text(editor)
        html_with_selection_removed.replace("\n", "")
        print(f"html_with_selection_removed : {html_with_selection_removed}")
        return  html_with_selection_removed
 
