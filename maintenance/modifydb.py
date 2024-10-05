"""
    Utilities to manage the database from text files and vice versa.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from database import Paragraph, engine, update_paragraph, get_paragraphs
import re

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

def store_lessons(list_of_files):
    """
    Store the lessons in "list_of_files" of type list in the directory "lessons/new".
    Lessons multiples of 7 are all considered dialogues in output but entries files do not contains dash "-". 

    Paramters:
        list_of_files: list of file names which should have the number of the lesson separate with white space as second token

    Returns:
        None
    """
    for fn in list_of_files:
        comp = re.split('\.| ', fn)
        lesson_nb = int(comp[1])
        new_file_name = f"lessons/new/L{str(lesson_nb).zfill(3)}.txt"
        txt_file = open(os.path.join("lessons/scanned", fn))
        lesson = txt_file.read()
        ll = lesson.split('\n\n')
        first_line = True
        newll = []
        ie = 0
        for l in ll:
            l = l.replace('\n', '')
            if l.find('\\') != -1:
                print(f"Leçon No : {lesson_nb}, {l}")
            if l.find('"') != -1:
                print(f"Leçon No : {lesson_nb}, {l}")
            l = l.replace('&quot;', '"')
            try:
                if l[0].isdigit():
                    ie += 1
            except IndexError:
                print(f"IndexError pour le fichier : {py_file_name} à la ligne : {ie}, {l}")
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


def has_dash_dialogue(sentence):
    for k, c in enumerate(sentence):
        if c.isdigit():
            pass
        elif c.isalpha():
            return False, sentence[k:]
        elif c == '-':
            return True, sentence[k+2:]
    raise
            
def get_french_paragraphs(lesson_nb):
    fn = f"lessons/new/L{str(lesson_nb).zfill(3)}.txt"
    lines = open(fn).readlines()
    paragraphs = [has_dash_dialogue(l.replace("\n", '')) for l in lines]
    return paragraphs

def rewrite_french_translation(lesson_nb):
    """
    Rewrite french paragraphs from text file in "lessons/new/" directory

    Parameters:
        lesson_nb : lesson number beetwen 1 and 100.

    Returns:
        None
    """


    french_paragraph = get_french_paragraphs(lesson_nb)
    with Session(engine) as session:
        stmt = select(Paragraph).where(Paragraph.lesson_nb == lesson_nb)
        for entry in session.scalars(stmt):
            #print(entry.line_nb, entry.section, entry.paragraph, entry.translation)
            print("db :", entry.translation, entry.has_dash_dialogue)
            print(french_paragraph[entry.line_nb][1])
            #entry.translation = french_paragraph[entry.line_nb][1]
            print('------')
        session.commit()
import database
print(database)