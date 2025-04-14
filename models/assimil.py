# assimil.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from typing import Optional, List
import datetime
from . import Base  # <- Importer la base commune

class Paragraph(Base):
    __tablename__ = "paragraphs"
    id: Mapped[int] = mapped_column(primary_key=True)
    level : Mapped[int]
    section : Mapped[int]
    lesson_nb : Mapped[int]
    line_nb : Mapped[int]
    paragraph: Mapped[str]
    translation: Mapped[str]
    has_dash_dialogue: Mapped[bool]
    grammar_indexes: Mapped[Optional[str]]
    data: Mapped[Optional[str]]
    def __repr__(self) -> str:
        return f"Paragraph(id={self.id!r}, level={self.level!r}, section={self.section!r}, lesson_nb={self.lesson_nb!r}, line_nb={self.line_nb!r}, paragraph ={self.paragraph!r}, grammar_indexes : {self.grammar_indexes!r}, data = {self.data!r})"

class LessonSession(Base):
    __tablename__ = "lesson_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped["User"] = relationship(back_populates="sessions")
    level: Mapped[int]
    lesson_nb: Mapped[int]
    date_time: Mapped[datetime.datetime]
    errors_number: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    errored_paragraphs : Mapped[List["MarkedParagraph"]] = relationship(
        back_populates="session", cascade="all, delete-orphan")
    def __repr__(self) -> str:
        return f"date time : {self.date_time!r}, level : {self.level!r}, lesson {self.lesson_nb!r} errors number : {self.errors_number!r}"

class MarkedParagraph(Base):
    __tablename__ = "marked_paragraphs"
    id: Mapped[int] = mapped_column(primary_key=True)
    paragraph: Mapped[str] 
    comment: Mapped[Optional[str]]
    line_nb : Mapped[int]
    session_id : Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"))
    session : Mapped["LessonSession"] = relationship(back_populates="errored_paragraphs")
    def __repr__(self) -> str:
        return f"Paragraph(id={self.id!r}, line={self.line_nb!r}, paragraph ={self.paragraph!r}, comment={self.comment!r})"

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    fullname: Mapped[str]
    email: Mapped[str]
    parameters: Mapped[str]
    parameters_version: Mapped[str]
    sessions: Mapped[List["LessonSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")
    def __repr__(self) -> str:
        return f"username : {self.username!r}, password : {self.password!r}, full name :{self.fullname}"

class GeneralParameters(Base):
    __tablename__ = "parameters"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str]
    instance: Mapped[str]

class GrammarNote(Base):
    __tablename__ = "grammar_note"
    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[int]
    lesson_nb: Mapped[int]
    note_number: Mapped[int]
    note: Mapped[str]
    def __repr__(self) -> str:
        return f"level : {self.level}, lessons_nb : {self.lesson_nb}, note_number : {self.note_number}, note : {self.note}"
