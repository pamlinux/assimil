import re
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from tonic_accent import get_paragraphs_from_audio_files, get_sentences, global_word_dict
from database import update_paragraph, get_single_paragraph, get_paragraphs_translation, engine, Paragraph
from translation import store_french_lesson

class ParagraphCorrectionItem(BaseModel):
    level : int
    lesson_nb : int
    line_nb: int
    has_dash_dialogue : bool | None = None
    paragraph : str | None = None
    translation : str | None = None

def get_correct_paragraphs_page(prog):
    print(f"prog : {prog}")
    if prog == "all":
        return get_all_incorrect_paragraphs_page()
    elif prog == "single":
        return get_correct_single_paragraph_page()
    
def get_paragraph_to_correct(item: ParagraphCorrectionItem):
    has_dash_dialogue, paragraph, translation = get_single_paragraph(item.level, item.lesson_nb, item.line_nb)
    return {"has_dash_dialogue" : has_dash_dialogue, "paragraph" : paragraph, "translation" : translation}

def get_correct_single_paragraph_page():
    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('correct_single_paragraph.html')
    html_text = template.render()
    return html_text
       
def get_all_incorrect_paragraphs_page():
    print("coucou")
    k= 0
    paragraphs_data = []
    stmt = select(Paragraph)
    session = Session(engine)
    for entry in session.scalars(stmt):
        tokens = re.findall(r"[\w]+", entry.paragraph)
        for token in tokens:
            if token.lower() not in global_word_dict:
                modified_paragraphs = get_sentences(entry.lesson_nb)
                print(f"token : {token} in lesson Nr : {entry.lesson_nb} at line {entry.line_nb}")
                paragraph_data = [entry.lesson_nb, entry.line_nb, entry.paragraph, modified_paragraphs[entry.line_nb]]
                paragraphs_data.append(paragraph_data)
                k += 1
    
    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('correct_paragraphs.html')
    html_text = template.render(
        paragraphs_nb = k,
        paragraphs_data = paragraphs_data
        )
    return html_text


def get_correct_paragraphs_from_mp3_page():
    k= 0
    paragraphs_data = []
    for lesson_nb in range(1, 101):
        mp3_paragraphs = get_paragraphs_from_audio_files(lesson_nb)
        modified_paragraphs = get_sentences(lesson_nb)
        for line_nb, mp3_paragraph in enumerate(mp3_paragraphs):
            tokens = re.findall(r"[\w]+", mp3_paragraph)
            for token in tokens:
                if not token in ['-', "'", '"', "[", "]", '¡', '!', '¿', '.', ',', '?', ';', ':', '…']:
                    if token.lower() not in global_word_dict:
                        paragraph_data = [lesson_nb, line_nb, mp3_paragraph, modified_paragraphs[line_nb]]
                        paragraphs_data.append(paragraph_data)
                        k += 1
    
    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('correct_paragraphs.html')
    html_text = template.render(
        paragraphs_nb = k,
        paragraphs_data = paragraphs_data
        )
    return html_text

def store_paragraph_correction(item: ParagraphCorrectionItem):
    print ("----- item ------", item)
    update_paragraph(item.level, item.lesson_nb, item.line_nb, item.has_dash_dialogue, item.paragraph, item.translation)
    paragraphs_translation = get_paragraphs_translation(item.level, item.lesson_nb)
    paragraphs_translation[item.line_nb][2] = item.translation
    store_french_lesson(item.level, item.lesson_nb, paragraphs_translation)

def get_correct_paragraphs_page_old():
    k= 0
    paragraphs_data = []
    for lesson_nb in range(1, 101):
        mp3_paragraphs = get_paragraphs_from_audio_files(lesson_nb)
        modified_paragraphs = get_sentences(lesson_nb)
        for line_nb, mp3_paragraph in enumerate(mp3_paragraphs):
            modified_paragraph = modified_paragraphs[line_nb].strip()
            if mp3_paragraph.strip() != modified_paragraph:
                paragraph_data = [lesson_nb, line_nb, mp3_paragraph, modified_paragraph]
                paragraphs_data.append(paragraph_data)
                k += 1
    
    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('correct_paragraphs.html')
    html_text = template.render(
        paragraphs_nb = k,
        paragraphs_data = paragraphs_data
        )
    return html_text
