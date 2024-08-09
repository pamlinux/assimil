import eyed3
import os
from pathlib import Path

from dataclasses import dataclass

from fastapi import FastAPI, Request, Response, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from tonic_accent import get_title, get_list_of_bold_sentences, store_lesson, update_lesson, correct_word

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

def get_title(filename):
    audiofile = eyed3.load(filename)
    return audiofile.tag.title
        
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
    print("numéro de la leçon : ", lesson_nb) 
    print(lesson_html)
    pretty_lesson_html = update_lesson(lesson_nb, lesson_html)
    
    return pretty_lesson_html

@app.post("/editor/correct/{lesson_nb}")
def form_correct_word(lesson_nb,  item: CorrectItem):
    word, syllabes = get_bold_word(item)
    lesson_html = item.lesson
    print(lesson_html)
    print("word to correct", word, syllabes)
    pretty_lesson_html = correct_word(lesson_nb, lesson_html, word, syllabes)
    return pretty_lesson_html

@app.get("/")
async def root():
    return {"message": "Hello World"}
