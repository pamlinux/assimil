import os
import re
import eyed3
import copy
from pathlib import Path
from pydantic import BaseModel
from lesson_parser import MyHTMLParser
from selection import extract_selection, extract_paragraphs
from database import store_lesson_errors, get_lessons_errors
import json

lessons_directory = f"Sentences"
db_directory = "db"

#lesson_directory = f"Sentences/L{str(lesson_nb).zfill(3)}-Spanish ASSIMIL"

word_dict_filename = "tonic_accent_word_dict"
word_dict_logfilename = "word_dict_logfile.log"
parser = MyHTMLParser()


class SelectionItem(BaseModel):
    anchorOffset : int
    focusOffset : int
    jsonDomString : str
    store: bool



def get_html_lesson_list():
    file_list = []
    m = "L[\d]{3}"
    p = re.compile(m)
    w = os.walk("Sentences/html")
    for (dirpath, dirnames, filenames) in w:
        for fn in filenames:
            if p.match(fn):
                file_list.append(fn)
    return file_list

def fill_word_tonic_accent_dict_from_html_files(filenames, word_dict):
    log_file_name = Path(db_directory, word_dict_logfilename)
    logfile = open(log_file_name, 'w')
    
    for fn in filenames:
        lesson_nb = int(fn[1:4])
        lesson = open(os.path.join(lessons_directory, "html", fn)).read()
        #print(f"Analyzing lesson {lesson_nb} with length {len(lesson)}")
        parser.analyze_lesson(lesson, lesson_nb)
        wd = parser.get_lesson_word_tonic_accent_dict()
        for word in wd:
            if not word in word_dict:
                word_dict[word] = wd[word]
            else:
                if wd[word] != word_dict[word]:
                    logfile.write(f"different tonic accent in lesson {lesson_nb} for word {word} {wd[word]} / {word_dict[word]} \n")

    for word in word_dict:
        logfile.write(f"{word} : {word_dict[word]}\n")
    logfile.close()

def fill_word_index_dict_from_html_files(filenames, word_dict):
    for fn in filenames:
        lesson_nb = int(fn[1:4])
        lesson = open(os.path.join(lessons_directory, "html", fn)).read()
        #print(f"Analyzing lesson {lesson_nb} with length {len(lesson)}")
        parser.analyze_lesson(lesson, lesson_nb)
        wd = parser.get_lesson_word_index_dict()
        for word in wd:
            if not word in word_dict:
                word_dict[word] = wd[word]
            else:
                word_dict[word].extend(wd[word])

def get_tonic_accent_word_dict():
    word_dict = {}
    lessons_filename = sorted(get_html_lesson_list())
    fill_word_tonic_accent_dict_from_html_files(lessons_filename, word_dict)
    return word_dict

def get_word_index_dict():
    word_dict = {}
    lessons_filename = sorted(get_html_lesson_list())
    fill_word_index_dict_from_html_files(lessons_filename, word_dict)
    return word_dict


global_word_dict = get_tonic_accent_word_dict()

def get_title(filename):
    audiofile = eyed3.load(filename)
    return audiofile.tag.title

def get_html_of_token(token, lesson_dict = {}):
    token_properties = lesson_dict.get(token.lower(), '')
    if not token_properties:
        token_properties = global_word_dict.get(token.lower(), '')
        if not token_properties:
            return token
    txt = ""
    index = 0
    for frag_struct in token_properties:
        frag_txt = token[index:index+len(frag_struct[0])]
        if frag_struct[1]:
            txt += "<b>" + frag_txt + "</b>"
        else:
            txt += frag_txt
        index += len(frag_struct[0])
    return txt

def get_bold_sentence(sentence, lesson_dict = {}):
    tokens = re.findall(r"[\w']+|[.,¡!¿:\-?;–]", sentence)
    bold_sentence = ""
    for index, token in enumerate(tokens):
        try:
            next_token = tokens[index + 1]
        except IndexError:
            next_token = ''
        bold_token = get_html_of_token(token, lesson_dict)
        bold_sentence += bold_token
        if not token in ".,¡!¿-?;:":
            if not next_token in ".,;!?-:":
                bold_sentence += ' '
        elif token in "¡-¿":
            pass
        else:
            bold_sentence += ' '
    return bold_sentence        
    
def get_sentences_from_audio_files(lesson_nb : int):
    lesson_directory = f"Sentences/L{str(lesson_nb).zfill(3)}-Spanish ASSIMIL"
    w = os.walk(lesson_directory)
    sentences_with_path = []
    for (dirpath, dirnames, filenames) in w:
        for fn in filenames:
            try:
                full_path = os.path.join(dirpath, fn)
                sentences_with_path.append([full_path, get_title(full_path)])
            except AttributeError:
                print(f"Attribute Error with file : {fn}")
        pathes, titles = zip(*sorted(sentences_with_path))
    return titles
    
def get_sentences(lesson_nb : int):
    lesson_filename = f"Sentences/html/L{str(lesson_nb).zfill(3)}.html"
    try:
        f = open(lesson_filename, "r")
        lines = f.readlines()
        f.close()
        lesson = ""
        for line in lines:
            lesson += line
        parser.analyze_lesson(lesson, lesson_nb)
        sentences = parser.get_sentences()
    except FileNotFoundError:
        sentences = get_sentences_from_audio_files(lesson_nb)
    return sentences

def get_html_sentences(lesson_nb : int):
    lesson_filename = f"Sentences/html/L{str(lesson_nb).zfill(3)}.html"
    try:
        f = open(lesson_filename, "r")
        lesson = f.read()
        f.close()
        paragraphs = extract_paragraphs(lesson)
    except FileNotFoundError:
        raise
    return paragraphs
        
def get_list_of_bold_sentences(lesson_nb):
    lesson_txt = get_sentences(lesson_nb)
    lesson_with_bold_sentences = []
    for sentence in lesson_txt:
        print(sentence)
        if sentence:
            lesson_with_bold_sentences.append(get_bold_sentence(sentence))
    return lesson_with_bold_sentences


def get_html_lesson(lesson_nb):
    lesson_html = ""
    list_of_bold_sentences = get_list_of_bold_sentences(lesson_nb)
    for sentence in list_of_bold_sentences:
        if sentence:
            lesson_html += "<p>" + sentence + "</p>"
    return lesson_html


def update_lesson(lesson_nb, lesson_html):
    pretty_lesson_html = ""
    parser.analyze_lesson(lesson_html, lesson_nb)
    lesson_word_dict = parser.get_lesson_word_tonic_accent_dict()
    sentences = parser.get_sentences()
    for sentence in sentences:
        if sentence:
            pretty_lesson_html += "<p>" + get_bold_sentence(sentence, lesson_word_dict) + "</p>"
    return pretty_lesson_html
        
def store_lesson(lesson_nb, lesson_html):
    filename = f"Sentences/html/L{str(lesson_nb).zfill(3)}.html"
    pretty_lesson_html = update_lesson(lesson_nb, lesson_html)
    file = open(filename, "w")
    file.write(pretty_lesson_html)
    file.close()

    parser.analyze_lesson(lesson_html, lesson_nb)
    lesson_word_dict = parser.get_lesson_word_tonic_accent_dict()
    print("lesson_word_dict", lesson_word_dict)
    for word in lesson_word_dict:
        global_word_dict[word] = lesson_word_dict[word]
    return pretty_lesson_html
       
def correct_word(lesson_nb, lesson_html, word, syllabes):
    pretty_lesson_html = ""
    parser.analyze_lesson(lesson_html, lesson_nb)
    lesson_word_dict = parser.get_lesson_word_tonic_accent_dict()
    global_word_dict[word] = syllabes
    lesson_word_dict[word] = syllabes
    sentences = parser.get_sentences()
    for sentence in sentences:
        if sentence:
            pretty_lesson_html += "<p>" + get_bold_sentence(sentence, lesson_word_dict) + "</p>"
    return pretty_lesson_html

    
def get_html_text(element, anchorOffset, focusOffset, mark_open = False, open_tag = None):
    text = ''
    #print(f"tag : {element['tagName']}, status : {element['status']}") 
    if element['tagName']:
        if element['tagName'] == 'p':
            if mark_open:
                text += '<' + element['tagName'] + '><mark>'
            else:
                text += '<' + element['tagName'] + '>'
        else:
            text += '<' + element['tagName'] + '>'
        if element['status'] == 'isAnchor':
            text += element['textContent'][:anchorOffset]
            text += '</' + element['tagName'] + '>' + '<mark>' + '<' + element['tagName'] + '>'
            text += element['textContent'][anchorOffset:]
            mark_open = True
        elif element['status'] == 'isAnchorAndFocus':
            text += element['textContent'][:anchorOffset]
            text += '<mark>'
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
                child_text, mark_open = get_html_text(child, anchorOffset, focusOffset, mark_open, element['tagName'])
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
                text += '</b><mark><b>'    
            else:
                text += '<mark>'
            text += element['textContent'][anchorOffset:]
            mark_open = True
        elif element['status'] == 'isAnchorAndFocus':
            text += element['textContent'][:anchorOffset]
            text += '<mark>' + element['textContent'][anchorOffset:focusOffset] + '</mark>'
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
    
def get_html_with_selection(div_element, anchorOffset, focusOffset):
    text = ""
    mark_open = False
    for element in div_element['children']:
        txt, mark_open = get_html_text(element, anchorOffset, focusOffset, mark_open)
        text += txt
    return text

def proceed_marked_selection(lesson_nb, item: SelectionItem):
    jsonDomString = item.jsonDomString
    editor = json.loads(jsonDomString);
    html_with_selection = get_html_with_selection(editor, item.anchorOffset, item.focusOffset)
    html_with_selection = html_with_selection.replace("\n", "")
    marked_lines_numbers, sentences = extract_selection(html_with_selection)
    print(marked_lines_numbers)
    print(sentences)
    if item.store:
        store_lesson_errors(lesson_nb, sentences, marked_lines_numbers)
    return html_with_selection

def get_lessons_with_errors(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None):
    errors = get_lessons_errors(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None)
    lessons = {}
    
    for lesson_nb in errors:
        lessons[lesson_nb] = {}
        sentences = get_html_sentences(lesson_nb)
        for date in errors[lesson_nb]:
            lesson = []
            for k, sentence in enumerate(sentences):
                if k in errors[lesson_nb][date]:
                    lesson.append(errors[lesson_nb][date][k])
                else:
                    lesson.append(sentences[k])
            lessons[lesson_nb][date] = lesson
    return lessons

def get_history(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None):
    lessons = get_lessons_with_errors(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None)
    rows = []
    th_rows = []
    col_nb = 0
    for lesson_nb in lessons:
        row=[]
        th_rows.append(lesson_nb)
        for date in lessons[lesson_nb]:
            row.append(date)
        rows.append(row)
        if len(row) > col_nb:
            col_nb = len(row) 
    return col_nb, th_rows, rows
