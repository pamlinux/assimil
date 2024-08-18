import re
import string
import os

from html.parser import HTMLParser

from collections import namedtuple

Word_properties = namedtuple("Word_properties", "tonic_accent index_ref")

def get_words(sentence):
    return re.sub('['+string.punctuation+'¿'+'¡'+']', ' ', sentence).split()

def get_syllables(sentence_fragments):

    syllables = []

    for f in sentence_fragments:
        frags = re.sub('['+string.punctuation+'¿'+'¡'+']', ' ', f[0]).split()
        for r in frags:
            syllables.append((r, f[1]))
    return syllables

def get_sentence_word_list(sentence, sentence_fragments):
    index = 0
    buffer = ""
    word_list = []
    tonic_accent = []

    words = get_words(sentence)
    syllables = get_syllables(sentence_fragments)

    for w in words:
        while index < 100:
            buffer += syllables[index][0]
            tonic_accent.append((syllables[index][0].lower(), syllables[index][1]))
            index += 1
            if buffer == w:
                word_list.append((w.lower(), tonic_accent))
                buffer = ""
                tonic_accent = []
                break
    return word_list

class MyHTMLParser(HTMLParser):
        
    def analyze_lesson(self, lesson, lesson_number):
        self.sentences = []
        self.sentences_fragments = []
        self.lesson_number = lesson_number
        self.bold_data = False
        self.feed(lesson)

    def get_lesson_word_dict(self):
        word_dict = {}
        if not hasattr(self, 'sentences'):
            return {}
        for i, s in enumerate(self.sentences):
            wl = get_sentence_word_list(s, self.sentences_fragments[i])
            for word, tonic_accent in wl:
                if not word in word_dict:
                    word_dict[word] = Word_properties(tonic_accent, [(self.lesson_number, i)])
                else:
                    word_dict[word].index_ref.append((self.lesson_number, i))
        return word_dict
        
        
    def handle_starttag(self, tag, attrs):
        if tag == "b":
            self.bold_data = True
        elif tag == "p":
            self.current_sentence = ""
            self.current_sentence_fragments = []
            #self.first_data = True


    def handle_endtag(self, tag):
        if tag == "b":
            self.bold_data = False
        elif tag == "p":
            self.sentences_fragments.append(self.current_sentence_fragments)
            self.sentences.append(self.current_sentence)
            
    def handle_data(self, data):
        #if self.first_data:
        #    self.first_data = False
            #data = data.split('-')[1]
        if hasattr(self, "current_sentence"):
            self.current_sentence_fragments.append((data, self.bold_data))
            self.current_sentence += data

    def get_sentences(self):
        return self.sentences
