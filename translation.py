
from html.parser import HTMLParser

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




def get_list_of_translated_sentences_lesson_54():
    lesson_file = f"Sentences/translation/L{str(54).zfill(3)}.html"
    f = open(lesson_file)
    lesson = f.read()
    parser = SimpleParser()
    parser.analyze_lesson(lesson)
    
    return parser.get_sentences()

import importlib

def get_french_lesson(lesson_nb):
    module = importlib.import_module(f"lessons.L{str(lesson_nb).zfill(3)}")
    if hasattr(module, 'exercise1_correction'):
        return module.lesson, module.exercise1_correction
    else:
        return module.lesson, []
