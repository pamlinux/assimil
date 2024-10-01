import importlib

from html.parser import HTMLParser
from database import get_paragraphs_translation

class SimpleParser(HTMLParser):
    def analyze_lesson(self, lesson):
        self.sentences = []
        self.data = ""
        self.feed(lesson)


    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.data = ""
        else:
            print("--------- tag", tag)
            raise

    def handle_endtag(self, tag):
        if tag == "p":
            self.sentences.append(self.data)
        else:
            raise
    
    def handle_data(self, data):
        self.data += data

    def get_sentences(self):
        return self.sentences


def get_french_lesson(lesson_nb):
    paragraphs = get_paragraphs_translation(lesson_nb)
    lesson = [paragraphs[0][2], paragraphs[1][2]]
    exercise1_correction = []
    writed_line_number = 1
    for line_nb in sorted(paragraphs.keys())[2:]:
        if paragraphs[line_nb][0] == 1: # if paragraph is in section 1
            text = str(writed_line_number)
            if paragraphs[line_nb][1]: # if paragraph no line_nb has dash dialogue
                text += '- '
            else:
                text += ' '
            lesson.append(text + paragraphs[line_nb][2].replace('"', "&quot;"))
            writed_line_number += 1
        else:
            exercise1_correction.append(paragraphs[line_nb][2].replace('"', "&quot;"))

    return lesson, exercise1_correction
 

    if hasattr(module, 'exercise1_correction'):
        for paragraph in module.exercise1_correction:
            exercise1_correction.append(paragraph.replace('"', "&quot;"))
    return lesson, exercise1_correction



def get_french_lesson_old(lesson_nb):
    module = importlib.import_module(f"lessons.L{str(lesson_nb).zfill(3)}")
    lesson = []
    exercise1_correction = []
    for paragraph in module.lesson:
        lesson.append(paragraph.replace('"', "&quot;"))
    if hasattr(module, 'exercise1_correction'):
        for paragraph in module.exercise1_correction:
            exercise1_correction.append(paragraph.replace('"', "&quot;"))
    return lesson, exercise1_correction

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


def store_french_lesson(lesson_nb, paragraphs):
    text = paragraphs[0][2]
    text += '\n' + paragraphs[1][2]

    writed_line_number = 1
    for line_nb in sorted(paragraphs.keys())[2:]:
        if paragraphs[line_nb][0] == 1: # if paragraph is in section 1
            text += '\n' + str(writed_line_number)
            if paragraphs[line_nb][1]: # if paragraph no line_nb has dash dialogue
                text += '- '
            else: # paragraph is in section 2 ie is in exercice 1
                text += ' '
        else:
            text += '\n '
        text += paragraphs[line_nb][2]
        writed_line_number += 1
    
    fn = f"lessons/new/L{str(lesson_nb).zfill(3)}.txt"
    f = open(fn, 'w')
    f.write(text)
    f.close()