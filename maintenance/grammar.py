import os
import json
from selection import SelectionItem
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from jinja2 import Environment, FileSystemLoader
from tonic_accent import get_spanish_lesson, get_bold_paragraph_with_note_numbers
from translation import get_french_lesson
from database import store_note_number, store_note, get_paragraphs
from paths import get_path      
from notes_parser import NotesParser

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

def get_html_with_grammar_number(item: GrammarNoteItem, level, lesson_nb):
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
                text += f'<sup> </sup>'
                text += fragment['textContent'][focus_offset:]
            else:
                text += fragment['textContent']
        elif fragment['tagName'] == 'sup':
            print(f"tag : {fragment['tagName']}, fragment : {fragment}")
            text += '<sup>' + fragment['textContent'] + '</sup>'
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
        elif fragment['tagName'] == 'sup':
            pass
        else:
            raise
    

    store_note_number(level, lesson_nb, line_nb, note_number, note_number_pos)

    paragraphs = get_paragraphs(level, lesson_nb)
    if  paragraphs is {}: raise
    p = paragraphs[line_nb]
 
    bold_paragraph = get_bold_paragraph_with_note_numbers(p[2], p[3])
    print(f"bold paragraph : {bold_paragraph}")

    lesson_french, exercise1_correction = get_french_lesson(level, lesson_nb)
    spanish_lesson, exercise1 = get_spanish_lesson(level, lesson_nb)

    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('test-grammar-html.jinja')
    div0 = template.render(
        lesson_nb = lesson_nb,
        lesson = spanish_lesson,
        exercise1 = exercise1,
        french_sentences = lesson_french + exercise1_correction
    )

    div0 = div0.replace('\n', '')
    return bold_paragraph
    #return 
    #return jsonable_encoder(response)
    #return json.dumps([clean_text, clean_text[:note_number_pos] + "<sup> 1</sup>" + clean_text[note_number_pos:], note_number_pos])

def store_all_notes():
    notes_directory = get_path("notes_directory")
    file_names = os.listdir("lessons/notes")
    parser = NotesParser()
    for fn in file_names:
        if fn[0] != '.':
            f = open(os.path.join(notes_directory, fn))
            notes = f.read()
            parser.analyze(notes)
            lesson_nb_string = ""
            for char in fn:
                if char.isdigit():
                    lesson_nb_string += char
            lesson_nb = int(lesson_nb_string)
            print(lesson_nb, fn)
            for note_number, note in parser.notes:
                store_note(lesson_nb, note_number, note)

def store_all_notes2(level = 0):
    if level == 0:
        level_prefix = "Basic"
    elif level == 1:
        level_prefix = "UsingSpanish"
    fn = os.path.join("lessons", level_prefix, "notes/Notes.html")
    notes_html = open(fn).read()
    parser = NotesParser()
    parser.analyze(notes_html)
    all_notes = parser.get_notes()
    for notes in all_notes:
        lesson_nb = notes[0]
        print(lesson_nb)
        for note in notes[1]:
            #print(note[0], "   ", note[1])
            store_note(level, lesson_nb, note[0], note[1])
    
def store_notes(lessons, level):
    if level == 0:
        level_prefix = "Basic"
    elif level == 1:
        level_prefix = "UsingSpanish"
    fn = os.path.join("lessons", level_prefix, "notes/Notes.html")
    notes_html = open(fn).read()
    parser = NotesParser()
    parser.analyze(notes_html)
    all_notes = parser.get_notes()
    print("coucou")
    for lesson_nb, notes in all_notes:
        print("lesson_nb : ", lesson_nb)
        if lesson_nb in lessons:
            print("++++++++++++++++", lesson_nb)
            for note_number, note in notes:
                print("+++++++++++++++", level, lesson_nb, note_number, note)
                store_note(level, lesson_nb, note_number, note)
    
    print("coucou à nouveau")


