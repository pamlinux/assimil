import eyed3
import os
from pathlib import Path

from dataclasses import dataclass

from fastapi import FastAPI, Request, Response, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from tonic_accent import get_tonic_accent_word_dict, get_list_of_bold_sentences, store_lesson

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

word_dict = get_tonic_accent_word_dict()

def get_title(filename):
    audiofile = eyed3.load(filename)
    return audiofile.tag.title
        
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
    
def get_html_sentences(lesson_nb : int):
    lesson_filename = f"Sentences/L{str(lesson_nb).zfill(3)}.txt"
    try:
        f = open(lesson_filename, "r")
        sentences = f.readlines()
        f.close()
    except FileNotFoundError:
        sentences = get_sentences(lesson_nb)
    return sentences

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

@app.get("/espagnol/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/editor/{lesson_nb}", response_class=HTMLResponse)
async def edit(request: Request, lesson_nb : int = 3):
    sentences = get_list_of_bold_sentences(lesson_nb)
    return templates.TemplateResponse(
        request=request, name="editor.html", context={"lesson_nb": lesson_nb, "sentences" : sentences})

@dataclass
class SimpleModel:
    ta: str = Form(None)
    da: str = Form(None)


@app.post("/editor/{lesson_nb}")
def form_post(lesson_nb, form_data: SimpleModel = Depends()):
    ta = form_data.ta
    lesson_html = form_data.da
    store_lesson(lesson_nb, lesson_html)
    
    return form_data

@app.get("/")
async def root():
    return {"message": "Hello World"}
