from pydantic import BaseModel
from typing import Optional, List
import datetime

from enum import Enum

class SubtitleVariant(str, Enum):
    es = "es"
    fr = "fr"
    eslong = "eslong"
    frlong = "frlong"

    def __str__(self):
        labels = {
            "es": "Espagnol",
            "fr": "Français",
            "eslong": "Espagnol (long)",
            "frlong": "Français (long)"
        }
        return labels.get(self.value, self.value)

class MediaType(str, Enum):
    series = "series"
    movie = "movie"

    def __str__(self):
        return {
            "series": "Série",
            "movie": "Film"
        }.get(self.value, self.value)

class SubtitleUpdate(BaseModel):
    media_id: int
    subtitle_variant: SubtitleVariant
    index: int
    text: str

class MediaMetadata(BaseModel):
    id: int | None = None
    title: str = ""
    media_type: MediaType | None = None
    season: int | None = None
    episode_number: int | None = None
    episode_title: str = ""
    disc_number: int | None = None
    video_filename: str | None = None
