from typing import List
import eyed3
import os
from pathlib import Path
from datetime import date, datetime
from dataclasses import dataclass
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Request, Response, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from database import get_errors, get_default_lesson, get_note
from tonic_accent import get_html_lessons_directory, get_lesson_audio_files_directory, get_title 
from tonic_accent import get_history, get_single_lesson_with_errors, get_spanish_lesson
from tonic_accent import get_list_of_bold_sentences, store_lesson, update_lesson, correct_word
from pydantic import BaseModel
from selection import proceed_marked_selection, delete_marked_selection, SelectionItem
from selection import MarkedSentencesItem, store_second_phase_marked_sentences
from translation import get_french_lesson
from auth import get_current_user_username
from assimil import get_correct_paragraphs_page, ParagraphCorrectionItem, store_paragraph_correction 
from assimil import get_paragraph_to_correct
from paths import get_path
from maintenance.grammar import get_html_with_grammar_number, GrammarNoteItem
from database import NoSuchLesson, update_subtitle_french, get_es_and_fr_subtitles
from database import get_fr_subtitles, get_es_subtitles
from subtitles import get_subtitles_context, NoSuchTvSerie

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

class SubtitleUpdate(BaseModel):
    id: int
    french_text: str

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

favicon_path = 'favicon.ico'

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

def get_full_path(lesson_nb, paragraph_nb, level = 0):
    lessons_directory = get_lesson_audio_files_directory(level)
    if level == 0:
        lesson_directory = os.path.join(lessons_directory, f"L{str(lesson_nb).zfill(3)}-Spanish ASSIMIL")
    elif level == 1:
        lesson_directory = os.path.join(lessons_directory, f"L{str(lesson_nb).zfill(3)}-Using Spanish ASSIMIL")


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
    return pathes[paragraph_nb]

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

@app.get("/play_sentence/", response_class=HTMLResponse)
async def play_sentence(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    return templates.TemplateResponse(
        request=request, name="play_sentence.html", context={"lesson_nb": lesson_nb, "sentence_nb" : sentence_nb}
    )

#@app.get("/spanish/{lesson_nb}", response_class=HTMLResponse)
#async def display_lesson(request: Request, lesson_nb : int = 8):
#    lesson = get_list_of_bold_sentences(lesson_nb)
#    return templates.TemplateResponse(
#        request=request, name="lesson.html", context={"active" : "lessons", "lesson_nb": lesson_nb, "lesson" : lesson})

@app.get("/spanish/", response_class=HTMLResponse)
async def display_home(request: Request, lesson_nb : int = 8):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"active"  :"home"})

@app.get("/history/", response_class=HTMLResponse)
async def display_errors(request: Request):
    return templates.TemplateResponse(
        request=request, name="history.html", context= {"active" : "history", "date" : date.today()})

@app.post("/history/")
async def get_errors(item: ErrorItem):
    print("item", item)
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

def get_lesson_errors_context(level, lesson_nb, datetimekey):
    date_time = datetime.strptime(datetimekey, '%d-%m-%Y %H:%M:%S%f')
    lesson_french, exercise1_correction = get_french_lesson(level, lesson_nb)
    spanish_lesson, exercise1  = get_single_lesson_with_errors(lesson_nb, date_time)
    print(spanish_lesson, exercise1)
    date_time_string = date_time.strftime("%d-%m-%Y à %H:%M:%S")

    context = {
        "active" : "lesson-errors",
        "level" : level,
        "lesson_nb": lesson_nb,
        "date_time" : date_time_string,
        "lesson" : spanish_lesson,                                                        
        "exercise1" : exercise1,
        "french_sentences" : lesson_french + exercise1_correction
    }
    return context

@app.get("/lesson-errors/", response_class=HTMLResponse)
async def get_errors_list_date(request: Request, level: int, lesson_nb : int = 0, datetimekey : str = ""):
    context = get_lesson_errors_context(level, lesson_nb, datetimekey)
    return templates.TemplateResponse(request=request, name="lesson-errors.html", context= context)


@app.get("/history/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/basic/second-phase/audio/")
def get_audio_file(request: Request, lesson_nb: int, paragraph_nb: int):
    print("lesson_nb:", lesson_nb, "sentence_nb", paragraph_nb)
    sentence_path = get_full_path(lesson_nb, paragraph_nb, level = 0)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/basic/first-phase/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb, level = 0)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/lesson-errors/audio/")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb)
    print("sentence_path", sentence_path)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/basic/editor/{lesson_nb}", response_class=HTMLResponse)
async def edit(request: Request, lesson_nb : int = 3):
    sentences = get_list_of_bold_sentences(lesson_nb, level = 0)
    context = {
        "active" : "basic-editor",
        "level" : 0,
        "lesson_nb": lesson_nb,
        "sentences" : sentences
        }
    return templates.TemplateResponse(
        request=request, name="editor.html", context= context)

@app.get("/using_spanish/editor/{lesson_nb}", response_class=HTMLResponse)
async def edit(request: Request, lesson_nb : int = 3):
    sentences = get_list_of_bold_sentences(lesson_nb, level = 1)
    context = {
        "active" : "using-spanish-editor",
        "level" : 1,
        "lesson_nb": lesson_nb,
        "sentences" : sentences
        }
    return templates.TemplateResponse(
        request=request, name="editor.html", context=context)

@app.post("/editor/save/")
def form_save(level: int, lesson_nb: int, form_data: SimpleModel = Depends()):
    ta = form_data.ta
    lesson_html = form_data.da
    print("numéro de la leçon : ", lesson_nb) 
    print(lesson_html)
    pretty_lesson_html = store_lesson(level, lesson_nb, lesson_html)
    
    return pretty_lesson_html

@app.post("/editor/update/")
def form_update(level: int, lesson_nb: int, form_data: SimpleModel = Depends()):
    ta = form_data.ta
    lesson_html = form_data.da
    print("numéro de la leçon : ", lesson_nb) 
    print(lesson_html)
    pretty_lesson_html = update_lesson(level, lesson_nb, lesson_html)
    print(f"pretty lesson : {pretty_lesson_html}")
    return pretty_lesson_html

@app.post("/editor/correct/")
def form_correct_word(level: int, lesson_nb: int,  item: CorrectItem):
    word, syllabes = get_bold_word(item)
    lesson_html = item.lesson
    print(lesson_html)
    print("word to correct", word, syllabes)
    pretty_lesson_html = correct_word(level, lesson_nb, lesson_html, word, syllabes)
    return pretty_lesson_html

@app.get("/marker-editor/{lesson_nb}")
async def test_edit(request: Request, lesson_nb : int = 3):   
    sentences = get_list_of_bold_sentences(lesson_nb)
    return templates.TemplateResponse(
        request=request, name="marker-editor.html", context={"active" : "marker-editor" , "lesson_nb": lesson_nb, "sentences" : sentences})

@app.post("/marker-editor/{lesson_nb}")
async def test_ranges(lesson_nb, item: SelectionItem):
    print(f"SelectionItem item.markType : {item.markType}")
    return proceed_marked_selection(lesson_nb, item)

@app.post("/marker-editor/delete/{lesson_nb}")
async def test_ranges(lesson_nb, item: SelectionItem):
    return delete_marked_selection(lesson_nb, item)

def get_second_phase_contex(lesson_nb, level = 0):
    french, exercise1_correction = get_french_lesson(level, lesson_nb)
    print("--- lesson ---", french)
    print("--- exercise1_correction ---", exercise1_correction)
    spanish_sentences, exercise1 = get_spanish_lesson(level, lesson_nb)
    if level == 1:
        active = "using-spanish-second-phase"
    elif level == 0:
        active = "basic-second-phase"
    context = {
        "active" : active,
        "level" : level,
        "lesson_nb": lesson_nb,
        "lesson" : french,                                                        
        "exercise1_correction" : exercise1_correction,
        "spanish_paragraphs" : spanish_sentences + exercise1
    }
    return context

@app.get("/basic/second-phase/{lesson_nb}", response_class=HTMLResponse)
async def second_phase(request: Request, lesson_nb : int = 1):
    context = get_second_phase_contex(lesson_nb, level = 0)
    return templates.TemplateResponse(
        request=request, name="second-phase.html", context=context)

@app.get("/using_spanish/second-phase/{lesson_nb}", response_class=HTMLResponse)
async def second_phase(request: Request, lesson_nb : int = 1):
    context = get_second_phase_contex(lesson_nb, level = 1)
    return templates.TemplateResponse(
        request=request, name="second-phase.html", context=context)

@app.get("/basic/second-phase/", response_class=HTMLResponse)
async def second_phase(request: Request, lesson_nb : int = 1):
    lesson_nb = get_default_lesson()
    context = get_second_phase_contex(lesson_nb, level = 0)
    return templates.TemplateResponse(
        request=request, name="second-phase.html", context=context)

@app.get("/using_spanish/second-phase/", response_class=HTMLResponse)
async def second_phase(request: Request, lesson_nb : int = 1):
    lesson_nb = get_default_lesson(level = 1)
    print("+++++ lesson_nb : ", lesson_nb)
    context = get_second_phase_contex(lesson_nb, level = 1)
    return templates.TemplateResponse(
        request=request, name="second-phase.html", context=context)

def get_first_phase_context(lesson_nb, active="first-phase", level = 0):
    lesson_french, exercise1_correction = get_french_lesson(level, lesson_nb)
    print("------- lesson_nb : ", lesson_nb)
    spanish_lesson_and_execrice1 = get_spanish_lesson(level, lesson_nb)
    if spanish_lesson_and_execrice1:
        spanish_lesson, exercise1 = spanish_lesson_and_execrice1
    else:
        return None
    
    if level == 0:
        level_prefix = "basic"
    elif level == 1:
        level_prefix = "using_spanish"
    else:
        raise

    context = {
        "active" : active,
        "level" : level,
        "level_prefix" : level_prefix,
        "lesson_nb": lesson_nb,
        "lesson" : spanish_lesson,                                                        
        "exercise1" : exercise1,
        "french_sentences" : lesson_french + exercise1_correction
    }
    print(f"---- In get_first_phase_context, with level_prefix : {level_prefix}")
    return context

@app.get("/basic/first-phase/{lesson_nb}", response_class=HTMLResponse)
async def first_phase(request: Request, lesson_nb : int = 1):
    context = get_first_phase_context(lesson_nb, level = 0)
    return templates.TemplateResponse(
        request=request, name="first-phase.html", context=context)

@app.get("/basic/first-phase/", response_class=HTMLResponse)
async def first_phase_default(request: Request):
    lesson_nb = get_default_lesson()
    context = get_first_phase_context(lesson_nb, level = 0)
    return templates.TemplateResponse(
        request=request, name="first-phase.html", context=context)


@app.post("/marker-translation/{lesson_nb}")
async def store_second_phase_lesson(item: MarkedSentencesItem, lesson_nb: int = 1):
    print("In store_second_phase_lesson --------", item, lesson_nb)
    store_second_phase_marked_sentences(get_current_user_username(), lesson_nb, item)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test")
async def test():
    f = open("test/test.html")
    html_text = f.read()
    return html_text

@app.get("/correct-assimil-paragraphs/", response_class=HTMLResponse)
async def correct_paragraphs(prog: str = "all" ):
    return get_correct_paragraphs_page(prog)

@app.post("/correct-assimil-paragraphs/", )
async def store_assimil_paragraph_correction(item: ParagraphCorrectionItem):
    store_paragraph_correction(item)

@app.post("/fetch-stored-paragraph/")
async def get_single_paragraph_stored(item : ParagraphCorrectionItem):
    print(item)
    return get_paragraph_to_correct(item)

@app.post("/store-paragraph-changes/")
async def store_paragraph_changes(item : ParagraphCorrectionItem):
    store_paragraph_correction(item)
    print("coucou", item)
    return "OK"

def get_grammar_context(level, lesson_nb):
    lesson_french, exercise1_correction = get_french_lesson(level, lesson_nb)
    print("------- lesson_nb : ", lesson_nb)
    spanish_lesson_and_execrice1 = get_spanish_lesson(level, lesson_nb)
    if spanish_lesson_and_execrice1:
        spanish_lesson, exercise1 = spanish_lesson_and_execrice1
    else:
        return None

    context = {
        "level" : level,
        "lesson_nb": lesson_nb,
        "lesson" : spanish_lesson,                                                        
        "exercise1" : exercise1,
        "french_sentences" : lesson_french + exercise1_correction
    }
    return context

@app.get("/test-grammar/", response_class=HTMLResponse)
async def test_grammar(request: Request, level: int, lesson_nb : int = 1):
    context = get_grammar_context(level, lesson_nb)
    return templates.TemplateResponse(
        request=request, name="test-grammar.jinja", context=context)

@app.post("/grammar-note-numbers-editor/")
async def insert_grammar_note_number(level: int, lesson_nb: int, item: GrammarNoteItem):
    return get_html_with_grammar_number(item, level, lesson_nb)

@app.get("/grammar_note/", response_class=HTMLResponse)
async def get_errors_list_date(request: Request, level: int, lesson_nb : int = 0, note_nb : int = 0):
    print(f"lesson_nb : {lesson_nb}, note_nb : {note_nb}")
    return get_note(level, lesson_nb, note_nb)

@app.get("/using_spanish/first-phase/audio")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb, level = 1)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/using_spanish/first-phase/", response_class=HTMLResponse)
async def using_spanish_first_phase_default(request: Request):
    lesson_nb = get_default_lesson(level = 1)
    try:
        context = get_first_phase_context(lesson_nb, active = "using-spanish-first-phase", level = 1)
    except NoSuchLesson:
        return "No such lesson"
    return templates.TemplateResponse(
        request=request, name="first-phase.html", context=context)

@app.get("/using_spanish/first-phase/{lesson_nb}", response_class=HTMLResponse)
async def using_spanish_first_phase_default(request: Request, lesson_nb : int = 1):
    try: 
        context = get_first_phase_context(lesson_nb, active = "using-spanish-first-phase", level = 1)
    except NoSuchLesson:
        return "No such Lesson"
    return templates.TemplateResponse(
        request=request, name="first-phase.html", context=context)

@app.get("/subtitles/edit/{dvd}", response_class=HTMLResponse)
async def get_subtitles_of_television_serie(request: Request, dvd : int =1):
    try:
        context = get_subtitles_context(dvd)
        print("context : ", context)
    except NoSuchTvSerie:
        return("No such TV serie")
    return templates.TemplateResponse(
        request=request, name="subtitles.jinja", context=context)

@app.get("/subtitles")
def get_both_subtitles():
    return get_es_and_fr_subtitles(1)

@app.post("/subtitles/update")
def update_subtitle_in_database(updates: List[SubtitleUpdate]):
    print(updates)
    for update in updates:
        update_subtitle_french(update.id, update.french_text)
        print(update.id, update.french_text)


    #for update in updates:
    #    for subtitle in subtitles:
    #        update_subtitle(subtitle)
    #raise HTTPException(status_code=404, detail="Subtitle not found")
    return {"message": "Subtitle updated successfully"}

@app.get("/video_viewer")
async def get_video_a1_t00(request: Request):
    return templates.TemplateResponse(
        request=request, name="video_viewer.jinja", context={"dummy" : 0})


#VIDEO_PATH = "Movies/Aquí No Hay Quien Viva 1/A1_t00.m4v" 
VIDEO_PATH = "Movies/Aquí No Hay Quien Viva 1/A1_t00.m4v" 

def video_stream(start: int, end: int):
    with open(VIDEO_PATH, "rb") as video:
        video.seek(start)
        while start < end:
            chunk = video.read(min(4096, end - start))
            if not chunk:
                break
            yield chunk
            start += len(chunk)


@app.get("/simple-video.mp4")
async def serve_video(request: Request):
    file_size = os.path.getsize(VIDEO_PATH)
    
    range_header = request.headers.get("range")
    if range_header:
        range_start, range_end = range_header.replace("bytes=", "").split("-")
        start = int(range_start)
        end = int(range_end) if range_end else file_size - 1
    else:
        start, end = 0, file_size - 1

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }

    return StreamingResponse(video_stream(start, end + 1), headers=headers, status_code=206)



@app.get("/subtitles.srt")
def get_subtitles():
    return FileResponse("Movies/Aquí No Hay Quien Viva 1/a1_t00_es.vtt", media_type="text/vtt")

@app.get("/subtitles_es")
def get_es_only_subtitles():
    return get_es_subtitles(1)

@app.get("/subtitles_fr")
def get_fr_only_subtitles():
    return get_fr_subtitles(1)