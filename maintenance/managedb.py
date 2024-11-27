import os
import re
from pathlib import Path
from paths import get_path
from tonic_accent import get_paragraphs_from_audio_files
from database import store_paragraph

using_spanish_scanned_lessons_french_text_directory = "/Users/pam/assimil/lessons/UsingSpanish/scanned"
spanish_scanned_lessons_french_text_directory = "/Users/pam/assimil/lessons/spanish/scanned"

def get_pos_after_digits(s):
    """
        Explicit.

        Parameters:
            s : paragraph string

        Returns:
            position in s of the first non digit character.
    """
    for i, c in enumerate(s[1:]):
        if not c.isdigit():
            return i+1

def has_dash_dialogue(paragraph):
    for k, c in enumerate(paragraph):
        if c.isdigit():
            pass
        elif c.isalpha():
            return False, paragraph[k:]
        elif c == '-':
            return True, paragraph[k+2:]
    raise
 
def clean_paragraph(p):
    if p[:3] == "S00":
        para = p[10:]
    elif p[:3] == "T00":
        para = p[14:]
    elif p[:4] == "ST00":
        para = p[15:]
    elif p[:2] == "ST":
        para = p[5:]
    elif p[0] == "N":
        pos = p.find('-')
        para = p[pos+1:]
    else:
        para = p[4:]
    return para

def rewrite_french_text_lessons(level):
    """
    Store the lessons from the directory 'scanned_lesson_french_text_directory' to the database.
    Lessons multiples of 7 are all considered dialogues in output but entries files do not contains dash "-". 
    the files name should have the number of the lesson separate with white space as second token

    Paramters:
        level:  0 for basic Spanish
        level:  1 for practicing Spanish

    Returns:
        None
    """

    if level == 0:
        scanned_lessons_french_text_directory = spanish_scanned_lessons_french_text_directory
    elif level == 1 :
        scanned_lessons_french_text_directory = using_spanish_scanned_lessons_french_text_directory

    new_file_directory = os.path.join(Path(scanned_lessons_french_text_directory).parent.absolute(), 'new')

    for fn in os.listdir(scanned_lessons_french_text_directory):
        comp = re.split('\.| ', fn)
        lesson_nb = int(comp[1])
        new_file_name = os.path.join(new_file_directory, f"L{str(lesson_nb).zfill(3)}.txt")
        txt_file = open(os.path.join(scanned_lessons_french_text_directory, fn))
        lesson = txt_file.read()
        ll = lesson.split('\n\n')
        first_line = True
        newll = []
        ie = 0
        for l in ll:
            l = l.replace('\n', '')
            if l.find('\\') != -1:
                print(f"\\ found in leçon No : {lesson_nb}, {l}")
            if l.find('"') != -1:
                print(f"Leçon No : {lesson_nb}, {l}")
            l = l.replace('&quot;', '"')
            try:
                if l[0].isdigit():
                    ie += 1
            except IndexError:
                print(f"IndexError pour le fichier : {txt_file} à la ligne : {ie}, {l}")
            #newll.append(l.lstrip('0123456789 '))
            if first_line:
                l = l.replace('\ufeff', '')
                newll.append(l)
                first_line = False
            else:
                newll.append('\n' + l)

        lesson = newll[:ie+2]
        exercise1 = newll[ie+2:]
        text = ""
        if exercise1:
            for l in lesson:
                text += l
            text += "\nExercice 1 – Traduction"
            for l in exercise1:
                text += l
        else:
            for k,l in enumerate(lesson):
                if k > 1:
                    i = get_pos_after_digits(l)
                    text += l[:i] + '-' + l[i:]
                else:
                    text += l
        new_file = open(new_file_name, "w")
        new_file.write(text)
        new_file.close()

def get_french_lesson_from_file(lesson_nb, level=1):
    if level == 0:
        scanned_lessons_french_text_directory = spanish_scanned_lessons_french_text_directory
    elif level == 1 :
        scanned_lessons_french_text_directory = using_spanish_scanned_lessons_french_text_directory

    new_file_directory = os.path.join(Path(scanned_lessons_french_text_directory).parent.absolute(), 'new')
    french_lesson_fn = os.path.join(new_file_directory, f"L{str(lesson_nb).zfill(3)}.txt")
    txt_file = open(french_lesson_fn)
    lesson = txt_file.readlines()
    return lesson

def get_french_paragraph_elements(paragraph):
    dash_found = False
    p = ""
    number = ""
    for i, c in enumerate(paragraph):
        if c.isdigit():
            number += c
        elif c == '-':
            dash_found = True
            index = i + 2
            break
        else:
            if number:
                index = i + 1
            else:
                index = i
            break
            
    if number:
        number = int(number)
    return number, dash_found, paragraph[index:].replace("\n", "")

def store_all_lessons(level = 1):

    if level == 0:
        scanned_lessons_french_text_directory = spanish_scanned_lessons_french_text_directory
    elif level == 1 :
        scanned_lessons_french_text_directory = using_spanish_scanned_lessons_french_text_directory

    new_file_directory = os.path.join(Path(scanned_lessons_french_text_directory).parent.absolute(), 'new')

    for fn in os.listdir(new_file_directory):
        lesson_nb = int(fn[1:4])
        new_file_name = os.path.join(new_file_directory, fn)
        print(lesson_nb, new_file_name)
        #french_lesson = get_french_lesson_from_file(lesson_nb, level)
        spanish_lesson = get_paragraphs_from_audio_files(lesson_nb, level)
        french_lesson = open(new_file_name).readlines()
        for line_nb, fp in enumerate(french_lesson):
            #print(get_french_paragraph_elements(fp))
            number, has_dash_dialogue, french_paragraph = get_french_paragraph_elements(fp)
            sp = spanish_lesson[line_nb]
            if sp[0] == 'N':
                section = 0
            elif sp[0] == 'S':
                section = 1
            elif sp[0] == 'T':
                section = 2
            spanish_paragraph = clean_paragraph(sp)
            #print(line_nb, clean_paragraph((spanish_lesson[line_nb])))
            #store_paragraph
            print(level, lesson_nb, section, line_nb, has_dash_dialogue, spanish_paragraph, french_paragraph)
            store_paragraph(level, lesson_nb, section, line_nb, has_dash_dialogue, spanish_paragraph, french_paragraph)
            
def store_lessons(lessons_number, level = 1):

    if level == 0:
        scanned_lessons_french_text_directory = spanish_scanned_lessons_french_text_directory
    elif level == 1 :
        scanned_lessons_french_text_directory = using_spanish_scanned_lessons_french_text_directory

    new_file_directory = os.path.join(Path(scanned_lessons_french_text_directory).parent.absolute(), 'new')

    for lesson_nb in lessons_number:
        fn = f"L{str(lesson_nb).zfill(3)}.txt"
        new_file_name = os.path.join(new_file_directory, fn)
        print(lesson_nb, new_file_name)
        #french_lesson = get_french_lesson_from_file(lesson_nb, level)
        spanish_lesson = get_paragraphs_from_audio_files(lesson_nb, level)
        french_lesson = open(new_file_name).readlines()
        for line_nb, fp in enumerate(french_lesson):
            #print(get_french_paragraph_elements(fp))
            number, has_dash_dialogue, french_paragraph = get_french_paragraph_elements(fp)
            sp = spanish_lesson[line_nb]
            if sp[0] == 'N':
                section = 0
            elif sp[0] == 'S':
                section = 1
            elif sp[0] == 'T':
                section = 2
            spanish_paragraph = clean_paragraph(sp)
            #print(line_nb, clean_paragraph((spanish_lesson[line_nb])))
            #store_paragraph
            print(level, lesson_nb, section, line_nb, has_dash_dialogue, spanish_paragraph, french_paragraph)
            store_paragraph(level, lesson_nb, section, line_nb, has_dash_dialogue, spanish_paragraph, french_paragraph)
            

    
            


