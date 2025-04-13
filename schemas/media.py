from pydantic import BaseModel
from typing import Optional, List
import datetime

class MediaMetadata(BaseModel):
    title: str = ""
    media_type: str = ""
    disc_number: int | None = None
    season: int | None = None
    series_number: int | None = None
    series_title: str = ""
    video_file: str | None = None
    spanish_subtitles_file: str | None = None
    long_spanish_subtitles_file: str | None = None
    french_subtitles_file: str | None = None
    long_french_subtitles_file: str | None = None
