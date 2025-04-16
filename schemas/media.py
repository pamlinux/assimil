from pydantic import BaseModel
from typing import Optional, List
import datetime

class MediaMetadata(BaseModel):
    id: int | None = None
    title: str = ""
    media_type: str = ""
    season: int | None = None
    episode_number: int | None = None
    episode_title: str = ""
    disc_number: int | None = None
    video_filename: str | None = None
