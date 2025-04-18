from typing import List
from typing import Optional
import eyed3
import os
from pathlib import Path
from datetime import date, datetime
from dataclasses import dataclass
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, Body, Query
from fastapi import FastAPI, Request, Response, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
import shutil
import whisper
import tempfile
from main_menu import MENU_ITEMS
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
from database import NoSuchLesson, update_subtitle, fetch_subtitles_from_db, get_subtitles, search_media
from database import get_fr_subtitles, get_es_subtitles, get_es_and_fr_subtitles, get_media_titles
from subtitles import get_subtitles_context, NoSuchTvSerie, store_media, get_subtitle_vtt_path, get_video_path
from schemas.media import SubtitleUpdate, MediaMetadata

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

@app.get("/spanish/", response_class=HTMLResponse)
async def display_home(request: Request, lesson_nb : int = 8):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"active" : "home", "menu_items" : MENU_ITEMS})

@app.get("/basic/history/", response_class=HTMLResponse)
async def display_errors(request: Request):
    context = {
        "active" : "basic-history",
        "menu_items" : MENU_ITEMS,
        "date" : date.today()
    }
    return templates.TemplateResponse(
        request=request, name="history.html", context= context)

@app.get("/using-spanish/history/", response_class=HTMLResponse)
async def display_errors(request: Request):
    context = {
        "active" : "using-spanish-history",
        "menu_items" : MENU_ITEMS,
        "date" : date.today()
    }
    return templates.TemplateResponse(
        request=request, name="history.html", context= context)

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
        "menu_items" : MENU_ITEMS,
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
        "menu_items" : MENU_ITEMS,
        "level" : 0,
        "lesson_nb": lesson_nb,
        "sentences" : sentences
        }
    return templates.TemplateResponse(
        request=request, name="editor.html", context= context)

@app.get("/using-spanish/editor/{lesson_nb}", response_class=HTMLResponse)
async def edit(request: Request, lesson_nb : int = 3):
    sentences = get_list_of_bold_sentences(lesson_nb, level = 1)
    context = {
        "active" : "using-spanish-editor",
        "menu_items" : MENU_ITEMS,
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
    context = {
        "active" : "marker-editor" ,
        "menu_items" : MENU_ITEMS,
        "lesson_nb": lesson_nb,
        "sentences" : sentences
    }
    return templates.TemplateResponse(
        request=request, name="marker-editor.html", context = context)

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
        "menu_items" : MENU_ITEMS,
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

@app.get("/using-spanish/second-phase/{lesson_nb}", response_class=HTMLResponse)
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

@app.get("/using-spanish/second-phase/", response_class=HTMLResponse)
async def second_phase(request: Request, lesson_nb : int = 1):
    lesson_nb = get_default_lesson(level = 1)
    print("+++++ lesson_nb : ", lesson_nb)
    context = get_second_phase_contex(lesson_nb, level = 1)
    return templates.TemplateResponse(
        request=request, name="second-phase.html", context=context)

def get_first_phase_context(lesson_nb, active="basic-first-phase", level = 0):
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
        level_prefix = "using-spanish"
    else:
        raise

    context = {
        "active" : active,
        "menu_items" : MENU_ITEMS,
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

@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
   return templates.TemplateResponse(
        request=request, name="test-grid.jinja", context= {"dummy" : "dummy"})


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

@app.get("/using-spanish/first-phase/audio")
def get_audio_file(request: Request, lesson_nb : int = 8, sentence_nb : int = 1):
    print("lesson_nb:", lesson_nb, "sentence_nb", sentence_nb)
    sentence_path = get_full_path(lesson_nb, sentence_nb, level = 1)
    data = open(sentence_path, "rb").read()
    return Response(content=data, media_type="audio/mpeg")

@app.get("/using-spanish/first-phase/", response_class=HTMLResponse)
async def using_spanish_first_phase_default(request: Request):
    lesson_nb = get_default_lesson(level = 1)
    try:
        context = get_first_phase_context(lesson_nb, active = "using-spanish-first-phase", level = 1)
    except NoSuchLesson:
        return "No such lesson"
    return templates.TemplateResponse(
        request=request, name="first-phase.html", context=context)

@app.get("/using-spanish/first-phase/{lesson_nb}", response_class=HTMLResponse)
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

@app.post("/subtitles/update")
def update_subtitles_in_database(updates: List[SubtitleUpdate] = Body(...)):
    print(updates)
    for update in updates:
        update_subtitle(update.media_id, update.index, update.subtitle_variant, update.text)
        print(update.media_id, update.index, update.subtitle_variant, update.text)


    #for update in updates:
    #    for subtitle in subtitles:
    #        update_subtitle(subtitle)
    #raise HTTPException(status_code=404, detail="Subtitle not found")
    return {"status" : "ok", "message": "Subtitle updated successfully"}

@app.get("/video_viewer", response_class=HTMLResponse)
async def get_video_from_media_id(request: Request, media_id: int):
    return templates.TemplateResponse(
        request=request, name="video_viewer.jinja", context={"media_id" : media_id})

videos_directory = get_path("videos_directory")

def video_stream(video_path: str, start: int, end: int):
    with open(video_path, "rb") as video:
        video.seek(start)
        while start < end:
            chunk = video.read(min(4096, end - start))
            if not chunk:
                break
            yield chunk
            start += len(chunk)


@app.get("/simple-video.mp4")
async def serve_video(request: Request, media_id: int):
    video_path = get_video_path(media_id)
    file_size = os.path.getsize(video_path)
    
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

    return StreamingResponse(video_stream(video_path, start, end + 1), headers=headers, status_code=206)

@app.get("/subtitles.srt")
def get_subtitles_vtt_file(request: Request, media_id: int):
    print("request: ", request, "media_id: ", media_id)
    subtitle_vtt_path = get_subtitle_vtt_path(media_id)
    return FileResponse(subtitle_vtt_path, media_type="text/vtt")

@app.get("/subtitles_es")
def get_es_only_subtitles():
    return get_es_subtitles("media")

@app.get("/subtitles_fr")
def get_fr_only_subtitles():
    return get_fr_subtitles("media")

@app.get("/long_subtitles_es")
def get_es_only_long_subtitles():
    return get_es_subtitles("long")

@app.get("/long_subtitles_fr")
def get_fr_only_long_subtitles():
    return get_fr_subtitles("long")

@app.get("/subtitles")
def get_subtitles_by_media_id_and_variant(media_id: int, variant: str):
    variant = variant.lower()
    print("variant received", variant)
    allowed_variants = ["es", "fr", "eslong", "frlong"]
    if variant not in allowed_variants:
        raise HTTPException(status_code=400, detail="Invalid subtitle variant")

    print(media_id, variant)
    subtitles =  get_subtitles(media_id, variant)
    return subtitles
    #return {"status": "ok", "variant": variant}

@app.get("/search-media")
def search_media_in_db(request: Request):
    return templates.TemplateResponse(
        request=request, name="store-media.jinja", context={"dummy" : 0})

@app.post("/save-media")
async def save_media_in_db(media_metadata: MediaMetadata):
    try:
        print("In /save-media")

        print(media_metadata)
        store_media(media_metadata)
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-subtitle")
async def update_subtitle_text(subtitle: SubtitleUpdate):
    print(f"subtitle : {subtitle}")
    update_subtitle(subtitle.media_id, subtitle.index, subtitle.subtitle_variant, subtitle.text)

    return {"message": "Sous-titre mis à jour", "subtitle_variant": subtitle.subtitle_variant,  "text": subtitle.text}

@app.get("/test-audio/")
async def test_audio(request: Request):
    return templates.TemplateResponse(
        request=request, name="test-audio.html", context={"dummy" : "dummy"}
    )

model = whisper.load_model("base")  # ou "small", "medium", selon ta machine

@app.post("/transcribe-audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    print("POST /transcribe-audio received")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    result = model.transcribe(tmp_path)
    return JSONResponse({"text": result["text"]})

@app.get("/api/titles")
def get_titles_from_database(q: str = Query(..., min_length=1)):
    results = get_media_titles(q)
    print(f"{type(results)}, results: {results}")
    return JSONResponse(content=results)

@app.get("/video", response_class=HTMLResponse)
async def display_video_panel(request: Request):
    return templates.TemplateResponse(
        request=request, name="video_panel.jinja", context={
            "filters": {
                "title": "Aqu",
                "disc_number": 1,
                "media_type": "series",
                "season": 1,
                "episode_number": 1,
                "episode_title": ""
            }
        }
)

from fastapi import Request

@app.get("/video_viewer_partial", response_class=HTMLResponse)
def video_viewer_partial(request: Request, media_id: int):
    print("In video_viewer_partial, with media_id:", media_id)
    return templates.TemplateResponse("video_viewer.jinja", {
        "request": request,
        "media_id": media_id
    })

@app.post("/media_search", response_class=HTMLResponse)
def search_media_in_db(
    request: Request,
    media_metadata: MediaMetadata  # Pydantic model attendu
):
    print(media_metadata)
    results = search_media(media_metadata)
    print("results", results)
    return templates.TemplateResponse(
        "media_results.jinja",
        { "request": request, "results": results }
    )

#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))

