# dictionary.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from typing import Optional, List
import datetime
from . import Base  # <- Importer la base commune

class Word(Base):
    __tablename__ = "word_dict"
    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] 
    tonic_accent: Mapped[str]
    comment: Mapped[Optional[str]]
    index_ref_entries: Mapped[List["IndexEntry"]] = relationship(
        back_populates="word", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"Word(id={self.id!r}, word={self.word!r}, comment={self.comment!r})"

class IndexEntry(Base):
    __tablename__ = "word_index"
    id : Mapped[int] = mapped_column(primary_key=True)
    level : Mapped[int]
    lesson_nb : Mapped[int]
    line_nb : Mapped[int]
    position : Mapped[Optional[int]]
    word_id : Mapped[int] = mapped_column(ForeignKey("word_dict.id"))
    word : Mapped["Word"] = relationship(back_populates="index_ref_entries")
    def __repr__(self) -> str:
        return f"IndexEntry(id={self.id!r}, word={self.word!r}, word_id={self.word_id}, lesson={self.lesson!r}, line={self.line!r}), position={self.position!r}"
        
