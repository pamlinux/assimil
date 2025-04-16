from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from database import engine, Media

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/select-media", response_class=HTMLResponse)
def select_media(request: Request,
                 title: str = "",
                 disc_number: int = None,
                 media_type: str = "",
                 season: int = None,
                 episode_number: int = None,
                 episode_title: str = ""):
    
    filters = []
    if title:
        filters.append(Media.title.ilike(f"%{title}%"))
    if disc_number is not None:
        filters.append(Media.disc_number == disc_number)
    if media_type:
        filters.append(Media.media_type == media_type)
    if season is not None:
        filters.append(Media.season == season)
    if episode_number is not None:
        filters.append(Media.episode_number == episode_number)
    if episode_title:
        filters.append(Media.episode_title.ilike(f"%{episode_title}%"))

    stmt = select(Media)
    if filters:
        stmt = stmt.where(and_(*filters))

    with Session(engine) as session:
        results = session.scalars(stmt).all()
    
    return templates.TemplateResponse("media_search.jinja", {
        "request": request,
        "results": results,
        "filters": {
            "title": title,
            "disc_number": disc_number,
            "media_type": media_type,
            "season": season,
            "episode_number": episode_number,
            "episode_title": episode_title
        }
    })
