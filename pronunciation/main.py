from dataclasses import dataclass

import eyed3
import os
from pathlib import Path

from fastapi import FastAPI, Request, Response, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/form", response_class=HTMLResponse)
def form_get():
    return """
        <form method="post" onsubmit="copyContent()"> 
            <textarea id="input" name="ta" rows="2">very
            long
            textarea
            text</textarea>
            <div id="da" contentEditable="true">
            even <br/> longer <br/> div <br/> area <br/> text <br/>
            </div>
            <input type="hidden" id="hiddenInput" name="da">
            <input type="submit"/> 
        </form>

        <script>
        function copyContent() {
            var divContent = document.getElementById("da").innerText;
            document.getElementById("hiddenInput").value = divContent;
        }
        </script>
"""



@app.get("/espagnol/{lesson_nb}", response_class=HTMLResponse)
async def display_lesson(request: Request, lesson_nb : int = 8):
    f=open(f"lessons/L{str(lesson_nb).zfill(3)}.html")
    lesson = f.read()
    return templates.TemplateResponse(
        request=request, name="lesson.html", context={"lesson_nb": lesson_nb, "lesson" : lesson})

@app.get("/editor/{lesson_nb}", response_class=HTMLResponse)
async def edit(request: Request, lesson_nb : int = 8):
    return templates.TemplateResponse(
        request=request, name="editor.html", context={"lesson_nb": lesson_nb})


@dataclass
class SimpleModel:
    ta: str = Form(None)
    da: str = Form(None)


@app.post("/form")
def form_post(form_data: SimpleModel = Depends()):
    ta = form_data.ta
    da = form_data.da
    print(":::::::::> ta")
    print(ta)
    print(":::::::::> da")
    print(da)
    return form_data


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
