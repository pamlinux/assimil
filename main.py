import eyed3
import os
from pathlib import Path
from datetime import date, datetime
from dataclasses import dataclass

from fastapi import FastAPI, Request, Response, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from database import get_errors
from tonic_accent import get_title, get_list_of_bold_sentences, store_lesson, update_lesson, correct_word
from tonic_accent import SelectionItem, proceed_marked_selection, get_history, get_single_lesson_with_errors
from pydantic import BaseModel

@dataclass
class SimpleModel:
    ta: str = Form(None)
    da: str = Form(None)


class CorrectItem(BaseModel):
    focusNodeIsAnchorNode : bool
    anchorNode : str
    anchorNodeTag : str
    focusNode : str
    focusNodeTag : str
    anchorNextSibling : str
    anchorNextSiblingTag : str
    lesson : str

class ErrorItem(BaseModel):
        firstLesson : str
        lastLesson : str
        mostRecentLesson : str
        oldestLesson : str


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

def get_bold_word(item : CorrectItem):
    if item.focusNodeIsAnchorNode:
        syllables = [(item.focusNode, False)]
        word = item.focusNode
    elif item.anchorNodeTag == 'B':
        syllables = [(item.anchorNode, True), (item.focusNode, False)]
        word = item.anchorNode + item.focusNode
    elif item.focusNodeTag == 'B':
        syllables = [(item.anchorNode, False), (item.focusNode, True)]
        word = item.anchorNode + item.focusNode
    elif item.anchorNextSiblingTag == 'B':
         syllables = [(item.anchorNode, False), (item.anchorNextSibling, True), (item.focusNode, False)]
         word = item.anchorNode + item.anchorNextSibling + item.focusNode
    else:
        raise
    return word, syllables

def get_full_path(lesson_nb, sentence_nb):
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
    return pathes[sentence_nb]
    
@app.get("/play_sentence/", response_class=HTMLResponse)
async def play_sentence(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    return templates.TemplateResponse(
        request=request, name="play_sentence.html", context={"lesson_nb": lesson_nb, "sentence_nb" : sentence_nb}
    )

@app.get("/espagnol/{lesson_nb}", response_class=HTMLResponse)
async def display_lesson(request: Request, lesson_nb : int = 8):
    sentences = get_list_of_bold_sentences(lesson_nb)
    return templates.TemplateResponse(
        request=request, name="lesson.html", context={"lesson_nb": lesson_nb, "sentences" : sentences})

@app.get("/errors/", response_class=HTMLResponse)
async def display_errors(request: Request):
    return templates.TemplateResponse(
        request=request, name="errors.html", context={"date" : date.today()})

@app.post("/errors/")
async def get_errors(item: ErrorItem):
    end_date = datetime.strptime(item.mostRecentLesson, '%Y-%m-%d')
    end_of_day_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    lessons, rows = get_history(
        begin_lesson = int(item.firstLesson),
        end_lesson = int(item.lastLesson),
        begin_date = datetime.strptime(item.oldestLesson, '%Y-%m-%d'),
        end_date = end_of_day_datetime
    )
    env = Environment(loader = FileSystemLoader("templates"))
    template = env.get_template('errors_list.html')
    div0 = template.render(
        lessons = lessons,
        rows = rows
    )
    div0 = div0.replace('\n', '')
    return div0

@app.get("/lesson-errors/", response_class=HTMLResponse)
async def get_errors_list_date(request: Request, lesson : int = 0, datetimekey : str = ""):
    date_time = datetime.strptime(datetimekey, '%d-%m-%Y %H:%M:%S%f')
    date_time_string = date_time.strftime("%d-%m-%Y à %H:%M:%S")
    sentences = get_single_lesson_with_errors(lesson, date_time)
    return templates.TemplateResponse(
        request=request, name="lesson-errors.html", context={"lesson_nb": lesson, "date_time" : date_time_string, "sentences" : sentences})


@app.get("/errors/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/espagnol/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/lesson-errors/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb)
    print("sentence_path", sentence_path)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/editor/{lesson_nb}", response_class=HTMLResponse)
async def edit(request: Request, lesson_nb : int = 3):
    sentences = get_list_of_bold_sentences(lesson_nb)
    return templates.TemplateResponse(
        request=request, name="editor.html", context={"lesson_nb": lesson_nb, "sentences" : sentences})

@app.post("/editor/save/{lesson_nb}")
def form_save(lesson_nb, form_data: SimpleModel = Depends()):
    ta = form_data.ta
    lesson_html = form_data.da
    print("numéro de la leçon : ", lesson_nb) 
    print(lesson_html)
    pretty_lesson_html = store_lesson(lesson_nb, lesson_html)
    #store_lesson(lesson_nb, lesson_html)
    
    return pretty_lesson_html

@app.post("/editor/update/{lesson_nb}")
def form_update(lesson_nb, form_data: SimpleModel = Depends()):
    ta = form_data.ta
    lesson_html = form_data.da
    print("numéro de la lelesson-errorsçon : ", lesson_nb) 
    print(lesson_html)
    pretty_lesson_html = update_lesson(lesson_nb, lesson_html)
    print(f"pretty lesson : {pretty_lesson_html}")
    return pretty_lesson_html

@app.post("/editor/correct/{lesson_nb}")
def form_correct_word(lesson_nb,  item: CorrectItem):
    word, syllabes = get_bold_word(item)
    lesson_html = item.lesson
    print(lesson_html)
    print("word to correct", word, syllabes)
    pretty_lesson_html = correct_word(lesson_nb, lesson_html, word, syllabes)
    return pretty_lesson_html

@app.get("/history/errors-editor/{lesson_nb}")
async def test_edit(request: Request, lesson_nb : int = 3):   
    sentences = get_list_of_bold_sentences(lesson_nb)
    return templates.TemplateResponse(
        request=request, name="errors-editor.html", context={"lesson_nb": lesson_nb, "sentences" : sentences})

@app.post("/history/errors-editor/{lesson_nb}")
async def test_ranges(lesson_nb, item: SelectionItem):
    print(f"SelectionItem item.markType : {item.markType}")
    return proceed_marked_selection(lesson_nb, item)



@app.get("/")
async def root():
    return {"message": "Hello World"}
