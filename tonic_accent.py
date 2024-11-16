import os
import re
import eyed3
import copy
from pathlib import Path
from pydantic import BaseModel
from lesson_parser import MyHTMLParser
from selection import extract_selection, extract_paragraphs
from database import get_single_lesson_errors, get_lesson_sessions_history, get_paragraphs
import datetime
from paths import get_path

html_lessons_directory = get_path('html_lessons_directory')
databases_directory = get_path('databases_directory')

word_dict_logfilename = get_path('word_dict_logfilename')

parser = MyHTMLParser()


def get_html_lesson_list():
    file_list = []
    m = "L[\d]{3}"
    p = re.compile(m)
    w = os.walk(html_lessons_directory)
    for (dirpath, dirnames, filenames) in w:
        for fn in filenames:
            if p.match(fn):
                file_list.append(fn)
    return file_list

def fill_word_tonic_accent_dict_from_html_files(filenames, word_dict):
    log_file_name = Path(databases_directory, word_dict_logfilename)
    logfile = open(log_file_name, 'w')
    
    for fn in filenames:
        lesson_nb = int(fn[1:4])
        lesson = open(os.path.join(html_lessons_directory, fn)).read()
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
        lesson = open(os.path.join(html_lessons_directory, fn)).read()
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

def get_bold_paragraph(paragraph, lesson_dict = {}):
    tokens = re.findall(r"[\w]+", paragraph)
    bold_paragraph = ""
    index = 0
    for token in tokens:
        token_length = len(token)
        pos = paragraph.find(token, index)
        inter_token = paragraph[index:pos]
        bold_paragraph += inter_token + get_html_of_token(token, lesson_dict)
        index += len(inter_token) + token_length
    bold_paragraph += paragraph[index:]
    return bold_paragraph

def get_bold_paragraph_with_note_numbers(paragraph, note_numbers, lesson_dict = {}):
    note_positions = []
    bold_paragraph = ""
    index = 0
    if note_numbers:
        for n in note_numbers:
            if type(note_numbers[n]) is list:
                for pos in note_numbers[n]:
                    note_positions.append((pos, n))
            else:
                note_positions.append((note_numbers[n], n))
        note_positions.sort()
        np_index = 0
        np = note_positions[np_index][0]
    else:
        np = float('inf')
    tokens = re.findall(r"[\w]+", paragraph)

    for token in tokens:
        token_length = len(token)
        pos = paragraph.find(token, index)
        inter_token = paragraph[index:pos]
        bold_paragraph += inter_token + get_html_of_token(token, lesson_dict)
        if np <= pos + token_length:
            bold_paragraph += f"<sup onclick='(function(event) {{ displayNote({note_positions[np_index][1]}, event); }})(event)' class='assimil'> {note_positions[np_index][1]}</sup>"
            if np_index < len(note_positions) - 1:
                np_index += 1
                np = note_positions[np_index][0]
            else:
                np = float('inf')
        index += len(inter_token) + token_length
    bold_paragraph += paragraph[index:]
    if np != float('inf'):
        bold_paragraph += f"<sup onclick='(function(event) {{ displayNote({note_positions[np_index][1]}, event); }})(event)' class='assimil'> {note_positions[np_index][1]}</sup>"
    return bold_paragraph

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
    lesson_filename = os.path.join(html_lessons_directory, f"L{str(lesson_nb).zfill(3)}.html")
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
    lesson_filename = os.path.join(html_lessons_directory, f"L{str(lesson_nb).zfill(3)}.html")
    try:
        f = open(lesson_filename, "r")
        lesson = f.read()
        print("In get_html_sentences --- lesson : ", lesson)
        f.close()
        paragraphs = extract_paragraphs(lesson)
        print("In get_html_sentences ---", paragraphs)
    except FileNotFoundError:
        raise
    return paragraphs
        
def get_list_of_bold_sentences(lesson_nb):
    paragraphs = get_paragraphs(lesson_nb)
    lines_nb = sorted(paragraphs.keys())
    lesson_with_bold_sentences = []
    for k in lines_nb:
        lesson_with_bold_sentences.append(get_bold_paragraph(paragraphs[k][2]).replace('"', "&quot;"))
    return lesson_with_bold_sentences

def get_spanish_lesson(lesson_nb):
    paragraphs = get_paragraphs(lesson_nb)
    p0 = paragraphs[0]
    p1 = paragraphs[1]
    lesson = [get_bold_paragraph_with_note_numbers(p0[2], p0[3]), get_bold_paragraph_with_note_numbers(p1[2], p1[3])]
    exercise1_correction = []
    lesson_line_number = 1
    exercise1_correction_number = 0
    for line_nb in sorted(paragraphs.keys())[2:]:
        p = paragraphs[line_nb]
        if p[0] == 1:
            lesson.append([lesson_line_number, p[1], get_bold_paragraph_with_note_numbers(p[2], p[3]).replace('"', "&quot;")])
            lesson_line_number += 1
        else:
            exercise1_correction.append([exercise1_correction_number, p[1], get_bold_paragraph_with_note_numbers(p[2], p[3]).replace('"', "&quot;")])
            exercise1_correction_number += 1
    return lesson, exercise1_correction
 

def update_lesson(lesson_nb, lesson_html):
    pretty_lesson_html = ""
    parser.analyze_lesson(lesson_html, lesson_nb)
    lesson_word_dict = parser.get_lesson_word_tonic_accent_dict()
    sentences = parser.get_sentences()
    for sentence in sentences:
        if sentence:
            pretty_lesson_html += "<p>" + get_bold_paragraph(sentence, lesson_word_dict) + "</p>"
    return pretty_lesson_html
        
def store_lesson(lesson_nb, lesson_html):
    filename = os.path.join(html_lessons_directory, f"L{str(lesson_nb).zfill(3)}.html")
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
            pretty_lesson_html += "<p>" + get_bold_paragraph(sentence, lesson_word_dict) + "</p>"
    return pretty_lesson_html

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

def get_single_lesson_with_errors(lesson_nb, date_time):
    spanish_lesson = get_spanish_lesson(lesson_nb)
    errors = get_single_lesson_errors(lesson_nb, date_time)
    line_nb = 0
    for snb, section in enumerate(spanish_lesson):
        for pnb, paragraph in enumerate(section):
            if type(paragraph) is str:
                print(snb, pnb, line_nb, spanish_lesson[snb][pnb])
                if line_nb in errors:
                    spanish_lesson[snb][pnb] = errors[line_nb]
            else:
                print(snb, pnb, line_nb, spanish_lesson[snb][pnb][2])
                if line_nb in errors:
                    spanish_lesson[snb][pnb][2] = errors[line_nb]
            line_nb += 1
    return spanish_lesson

def get_history(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None):
    sessions = get_lesson_sessions_history(begin_lesson, end_lesson, begin_date, end_date)

    rows = []
    lessons = []
    for lesson_nb in sessions:
        row=[]
        lessons.append(lesson_nb)
        for date_time in sessions[lesson_nb]:
            row.append((date_time, sessions[lesson_nb][date_time]))
        rows.append(row)
    return  lessons, rows
