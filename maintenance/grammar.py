import json
from selection import SelectionItem
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from jinja2 import Environment, FileSystemLoader
from tonic_accent import get_spanish_lesson
from translation import get_french_lesson
from database import store_note_number

class GrammarNoteItem(BaseModel):
    anchorOffset : int
    focusOffset : int
    editorDomString : str
    noteNumber : int
    lineNb : int

class GrammarNoteResponseItem(BaseModel):
    line_nb : int
    paragraph : str

def has_one_child_focus(element):
    if element['status'] != '':
        return True
    else:
        for child in element['children']:
            if has_one_child_focus(child):
                return True
    return False

def find_selection_focus_element(element):
    if element['tagName'] in ['p', 'h2']:
        if has_one_child_focus(element):
            return element
    else:
        for child in element['children']:
            result = find_selection_focus_element(child)
            if result:
                return result


def find_selection_elements(element):
    if element['status'] != '':
        print(element)
    for child in element['children']:
        find_selection_elements(child)

def get_html_with_grammar_number(item: GrammarNoteItem, lesson_nb):
    editor = json.loads(item.editorDomString)
    find_selection_elements(editor)
    focus_offset = item.focusOffset
    print(f"Anchor Offset : {item.anchorOffset}, Focus Offset : {item.focusOffset}")
    note_number = item.noteNumber
    element = find_selection_focus_element(editor)
    print(f"find_selection_focus_element returns : {element}")
    line_nb = item.lineNb

    text = ""
    if element['tagName'] == 'p':
        #line_nb = int(element['children'][0]['children'][0]['textContent'])
        line_text_fragments = element['children'][2]['children']
    elif element['tagName'] == 'h2':
        line_text_fragments = element['children']
        print(f"line_text_fragments : {line_text_fragments}")

    for fragment in line_text_fragments:
        if fragment['tagName'] in ['b', '']:
            if fragment['status'] in ['isFocus', 'isAnchorAndFocus']:
                text += fragment['textContent'][:focus_offset]
                text += '<sup> 1</sup>'
                text += fragment['textContent'][focus_offset:]
            else:
                text += fragment['textContent']
        else:
            raise
    print("------ text --------", text)
    clean_text = ""
    for fragment in line_text_fragments:
        print(f"fragment['tagName'] : {fragment['tagName']}, fragment['status'] : {fragment['status']}")
        if fragment['tagName'] == '':
            if fragment['status'] in ['isFocus', 'isAnchorAndFocus']:
                note_number_pos = len(clean_text) + focus_offset
            clean_text += fragment['textContent']
        elif fragment['tagName'] == 'b':
            if fragment['status'] in ['isFocus', 'isAnchorAndFocus']:
                raise
            for child in fragment['children']:
                if child['status'] in ['isFocus', 'isAnchorAndFocus']:
                    note_number_pos = len(clean_text) + focus_offset
                clean_text += child['textContent']
        else:
            raise
    
    print(f"{text}\n{clean_text[:note_number_pos]}<sup> {note_number}</sup>{clean_text[note_number_pos:]}")

    store_note_number(lesson_nb, line_nb, note_number, note_number_pos)

    lesson_french, exercise1_correction = get_french_lesson(lesson_nb)
    spanish_lesson, exercise1 = get_spanish_lesson(lesson_nb)

    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('test-grammar-html.jinja')
    div0 = template.render(
        lesson_nb = lesson_nb,
        lesson = spanish_lesson,
        exercise1 = exercise1,
        french_sentences = lesson_french + exercise1_correction
    )

    div0 = div0.replace('\n', '')
    return div0
    #return 
    #return jsonable_encoder(response)
    #return json.dumps([clean_text, clean_text[:note_number_pos] + "<sup> 1</sup>" + clean_text[note_number_pos:], note_number_pos])
