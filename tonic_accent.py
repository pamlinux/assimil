import os
import re
import eyed3
import copy

from lesson_parser import MyHTMLParser
lessons_directory = f"Sentences"

#lesson_directory = f"Sentences/L{str(lesson_nb).zfill(3)}-Spanish ASSIMIL"

word_dict_filename = "tonic_accent_word_dict.dat"

parser = MyHTMLParser()

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

def get_word_dict_from_html_files(filenames):
    word_dict = {}
    for fn in filenames:
        print(fn)
        lesson = open(os.path.join(lessons_directory, "html", fn)).read()
        print(fn, " : ", len(lesson))
        parser.analyze_lesson(lesson)
        wd = parser.get_lesson_word_dict()
        for w in wd:
            if not w in word_dict:
                word_dict[w] = wd[w]

    return word_dict

lessons_filename = sorted(get_html_lesson_list())
print(lessons_filename)
global_word_dict = get_word_dict_from_html_files(lessons_filename)

def get_tonic_accent_word_dict():
    return global_word_dict

def get_title(filename):
    audiofile = eyed3.load(filename)
    return audiofile.tag.title

def get_html_of_token(token, word_dict):
    token_struct = word_dict.get(token.lower(), '')
    if not token_struct:
        return token
    else:
        txt = ""
        index = 0
        for frag_struct in token_struct:
            frag_txt = token[index:index+len(frag_struct[0])]
            if frag_struct[1]:
                txt += "<b>" + frag_txt + "</b>"
            else:
                txt += frag_txt
            index += len(frag_struct[0])
        return txt

def get_bold_sentence(sentence, word_dict):
    tokens = re.findall(r"[\w']+|[.,¡!¿\-?;–]", sentence)
    bold_sentence = ""
    for index, token in enumerate(tokens):
        try:
            next_token = tokens[index + 1]
        except IndexError:
            next_token = ''
        bold_token = get_html_of_token(token, word_dict)
        bold_sentence += bold_token
        if not token in ".,¡!¿-?;":
            if not next_token in ".,;!?-":
                bold_sentence += ' '
        elif token in "¡-¿":
            pass
        else:
            bold_sentence += ' '
    return bold_sentence        
    
def get_sentences(lesson_nb : int):
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

def get_list_of_bold_sentences_with_specific_dict(lesson_nb, word_dict):
    lesson_txt = get_sentences(lesson_nb)
    lesson_with_bold_sentences = []
    for sentence in lesson_txt:
        print(sentence)
        if sentence:
            lesson_with_bold_sentences.append(get_bold_sentence(sentence, word_dict))
    return lesson_with_bold_sentences
    
def get_list_of_bold_sentences(lesson_nb):
    return get_list_of_bold_sentences_with_specific_dict(lesson_nb, global_word_dict)


def get_html_lesson(lesson_nb):
    lesson_html = ""
    list_of_bold_sentences = get_list_of_bold_sentences(lesson_nb)
    for sentence in list_of_bold_sentences:
        if sentence:
            lesson_html += "<p>" + sentence + "</p>"
    return lesson_html


def update_lesson(lesson_nb, lesson_html):
    pretty_lesson_html = ""
    parser.analyze_lesson(lesson_html)
    wd = parser.get_lesson_word_dict()
    local_word_dict = copy.deepcopy(global_word_dict)
    for w in wd:
        if not w in local_word_dict:
            local_word_dict[w] = wd[w]

    sentences = parser.get_sentences()
    for sentence in sentences:
        if sentence:
            pretty_lesson_html += "<p>" + get_bold_sentence(sentence, local_word_dict) + "</p>"
    return pretty_lesson_html
        
def store_lesson(lesson_nb, lesson_html):
    filename = f"Sentences/html/L{str(lesson_nb).zfill(3)}.html"
    pretty_lesson_html = update_lesson(lesson_nb, lesson_html)
    file = open(filename, "w")
    file.write(pretty_lesson_html)
    file.close()
    return pretty_lesson_html
       
    
