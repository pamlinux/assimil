# models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from typing import Optional, List
import datetime
from . import Base  # <- Importer la base commune

class Media(Base):
    __tablename__ = 'media'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    media_type: Mapped[str] # "movie" or "series"
    season: Mapped[Optional[int]]
    series_number: Mapped[Optional[int]] # Number of the series
    episode_title: Mapped[Optional[str]]
    disc_number: Mapped[Optional[int]] # Number of the DVD or Blu-ray
    video_filename: Mapped[Optional[str]]
    subtitles: Mapped[List["Subtitle"]] = relationship(
        back_populates="media", cascade="all, delete-orphan")

class Subtitle(Base):
    __tablename__ = 'subtitles'
    id: Mapped[int] = mapped_column(primary_key=True)
    index: Mapped[int]
    subtitle_type: Mapped[str]  # "media" or "long"
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"))
    media: Mapped["Media"] = relationship(back_populates="subtitles")
    start_time: Mapped[datetime.time]
    end_time: Mapped[datetime.time]
    spanish_text: Mapped[str]
    french_text: Mapped[Optional[str]]
    __table_args__ = (UniqueConstraint('media_id', 'index', 'subtitle_type', name='unique_media_subtitle_index_type'),)
