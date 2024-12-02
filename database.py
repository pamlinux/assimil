from typing import List
from typing import Optional
import datetime
import pickle
import pytz
from sqlalchemy import ForeignKey, select, String, and_, desc, exc
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from paths import get_path
import yaml

class NoSuchLesson(Exception):
    pass

class Base(DeclarativeBase):
    pass

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
    
def get_database_engine(name, echo=True):
    engine = create_engine(name, echo = echo)   
    Base.metadata.create_all(engine) 
    return engine

database_name = "sqlite:////Users/pam/assimil/db/assimil_spanish_mnt3.db"
#database_name = get_path('database_name')

global engine
engine = get_database_engine(database_name, False)

def fill_word_table(tonic_accent_word_dict, word_index_dict = {}):
    with Session(engine) as session:
        for word in tonic_accent_word_dict:
            entries = []
            if word in word_index_dict:
                for entry in word_index_dict[word]:
                    lesson, line = entry
                    entries.append(IndexEntry(lesson=lesson, line=line))
            word_obj = Word(
                word=word, 
                tonic_accent=pickle.dumps(tonic_accent_word_dict[word]),
                index_ref_entries=entries
            )
            session.add_all([word_obj])
        session.commit()

def get_tonic_accent_word_dict():
    stmt = select(Word)
    word_dict = {}
    with Session(engine) as session:
        for word in session.scalars(stmt):
            word_dict[word.word] = pickle.loads(word.tonic_accent)
    return word_dict

def get_word_index_dict():
    stmt = select(IndexEntry)
    word_index_dict = {}
    with Session(engine) as session:
        for entry in session.scalars(stmt):
            if not entry.word.word in word_index_dict:
                word_index_dict[entry.word.word] = [(entry.lesson, entry.line)]
            else:
                word_index_dict[entry.word.word].append((entry.lesson, entry.line))
    return word_index_dict

def store_lesson_errors(username, lesson_number, errored_paragraphs, date_time = None):
    if not date_time:
       date_time = datetime.datetime.now()
    with Session(engine) as session:
        stmt = select(User).where(User.username == username)
        user = session.scalars(stmt).one()
        errored_paragraphs_list = []
        for line_nb in errored_paragraphs:
            print("----", line_nb, "------")
            errored_paragraphs_list.append(MarkedParagraph(
                line_nb = line_nb,
                paragraph = errored_paragraphs[line_nb]
            ))
        l_obj = LessonSession(
            user = user,
            level = 0,
            lesson_nb = lesson_number,
            date_time = date_time,
            errors_number = len(errored_paragraphs_list),
            errored_paragraphs = errored_paragraphs_list
        )
        session.add(l_obj)
        session.commit()


def get_single_lesson_errors(lesson_nb, date_time : datetime.datetime):
    print(f"----- In get_single_lesson_errors  date : {date_time}, of type {type(date_time)}")
    stmt = select(LessonSession).where(
                LessonSession.lesson_nb == lesson_nb,
                LessonSession.date_time == date_time
            )

    errors = {}
    with Session(engine) as session:
        for lesson_session in session.scalars(stmt):
            for paragraph_entry in lesson_session.errored_paragraphs:
                errors[paragraph_entry.line_nb] = paragraph_entry.paragraph

    return errors
   
def get_errors(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None):
    if not begin_date: begin_date = datetime.datetime.min
    if not end_date: end_date = datetime.datetime.max
    stmt = select(MarkedParagraph).where(
                    and_(
                        MarkedParagraph.date_time >= begin_date,
                        MarkedParagraph.date_time <= end_date,
                        MarkedParagraph.lesson >= begin_lesson,
                        MarkedParagraph.lesson <= end_lesson,
                    )
                )
    errors = []
    with Session(engine) as session:
        for entry in session.scalars(stmt):
            errors.append(entry.paragraph)
    return errors

def get_lesson_sessions_history(begin_lesson_nb = 1, end_lesson_nb = 100, begin_date = None, end_date = None, level = -1):
    print(f"----------------- begin_date : {begin_date}")
    print(f"----------------- end_date : {end_date}")
    if not begin_date: begin_date = datetime.datetime.min
    if not end_date: end_date = datetime.datetime.max
    sessions = {}
    if level in [0, 1]:
        stmt = select(LessonSession).where(
                    and_(
                        LessonSession.level == level,
                        LessonSession.date_time >= begin_date,
                        LessonSession.date_time <= end_date,
                        LessonSession.lesson_nb <= end_lesson_nb,
                        LessonSession.lesson_nb >= begin_lesson_nb
                    )
            )
    else:
        stmt = select(LessonSession).where(
                    and_(
                        LessonSession.date_time >= begin_date,
                        LessonSession.date_time <= end_date,
                        LessonSession.lesson_nb <= end_lesson_nb,
                        LessonSession.lesson_nb >= begin_lesson_nb
                    )
            )

    with Session(engine) as session:
        for entry in session.scalars(stmt):
            if (entry.level, entry.lesson_nb) in sessions:
                sessions[(entry.level, entry.lesson_nb)][entry.date_time] = entry.errors_number
            else:
                sessions[(entry.level, entry.lesson_nb)] = {entry.date_time : entry.errors_number}
    return sessions

def get_default_lesson(level = 0):
    if level == 0:
        last_lesson_session = Session(engine).query(LessonSession).order_by(desc('date_time')).first()
        return last_lesson_session.lesson_nb
    elif level == 1:
        return 1

def store_paragraph(level, lesson_nb, section, line_nb, has_dash_dialogue, paragraph, translation = None):
    stmt = select(Paragraph).where(
        and_(
            Paragraph.level == level,
            Paragraph.lesson_nb == lesson_nb,
            Paragraph.line_nb == line_nb
            )
    )
    print("level :", level, "lesson_nb : ", lesson_nb, "line_nb :", line_nb)
    with Session(engine) as session:
        try:
            entry = session.scalars(stmt).one()
            entry.section = section
            entry.has_dash_dialogue = has_dash_dialogue
            entry.paragraph = paragraph
            entry.translation = translation
        except exc.NoResultFound:
            print("titi")
            entry = Paragraph(
                level = level,
                lesson_nb = lesson_nb,
                section = section,
                line_nb = line_nb,
                has_dash_dialogue = has_dash_dialogue,
                paragraph = paragraph,
                translation = translation
            )
            session.add(entry)
        session.commit()

def update_paragraph(level, lesson_nb, line_nb, has_dash_dialogue, paragraph, translation = None, section = None):
    stmt = select(Paragraph).where(
        and_(
            Paragraph.level == level,
            Paragraph.lesson_nb == lesson_nb,
            Paragraph.line_nb == line_nb
            )
    )

    with Session(engine) as session:
        entry = session.scalars(stmt).one()
        if section:
            entry.section = section
        if translation:
            entry.translation = translation
        entry.paragraph = paragraph
        entry.has_dash_dialogue = has_dash_dialogue
        session.commit()

def get_paragraphs(level, lesson_nb):
    stmt = select(Paragraph).where(
        and_(
            Paragraph.lesson_nb == lesson_nb,
            Paragraph.level == level
        )
    )
    
    paragraphs = {}
    with Session(engine) as session:
        for entry in session.scalars(stmt):
            if entry.grammar_indexes:
                note_numbers = yaml.safe_load(entry.grammar_indexes)
            else:
                note_numbers = None
            paragraphs[entry.line_nb] = [entry.section, entry.has_dash_dialogue, entry.paragraph, note_numbers]
    if paragraphs == {}: raise NoSuchLesson
    return paragraphs

def get_single_paragraph(level, lesson_nb, line_nb):
    stmt = select(Paragraph).where(
        and_(
            Paragraph.level == level,
            Paragraph.lesson_nb == lesson_nb,
            Paragraph.line_nb ==line_nb
            )
    )
    with Session(engine) as session:
        entry = session.scalars(stmt).one()
        return entry.has_dash_dialogue, entry.paragraph, entry.translation
    
def get_paragraphs_translation(level, lesson_nb):
    stmt = select(Paragraph).where(
        and_(
            Paragraph.level == level,
            Paragraph.lesson_nb == lesson_nb
            )
    )

    paragraphs_translation = {}
    with Session(engine) as session:
        for entry in session.scalars(stmt):
            paragraphs_translation[entry.line_nb] =  [entry.section, entry.has_dash_dialogue, entry.translation]

    return paragraphs_translation

def store_note_number(level, lesson_nb, line_nb, note_number, note_number_pos):
    stmt = select(Paragraph).where(
        and_(
            Paragraph.level == level,
            Paragraph.lesson_nb == lesson_nb,
            Paragraph.line_nb == line_nb
            )
    )

    with Session(engine) as session:
        entry = session.scalars(stmt).one()
        grammar_indexes_string = entry.grammar_indexes
        if grammar_indexes_string:
            grammar_indexes = yaml.safe_load(grammar_indexes_string)
            if note_number in grammar_indexes:
                if type(grammar_indexes[note_number]) is list:
                    grammar_indexes[note_number].append(note_number_pos)
                else:
                    print("--------- coucou in store_note_number ----------", "grammar_indexes :", grammar_indexes)
                    grammar_indexes[note_number] = [grammar_indexes[note_number], note_number_pos]

            else:
                grammar_indexes[note_number] = note_number_pos
        else:
            grammar_indexes = {note_number : note_number_pos}
        entry.grammar_indexes = yaml.dump(grammar_indexes)
        session.commit()


def store_note(level, lesson_nb, note_number, note):
    stmt = select(GrammarNote).where(
        and_(
            GrammarNote.level == level,
            GrammarNote.lesson_nb == lesson_nb,
            GrammarNote.note_number == note_number
        )
    )
    with Session(engine) as session:
        try:
            entry = session.scalars(stmt).one()
            entry.note = note
        except exc.NoResultFound:
            entry = GrammarNote(
                level = level,
                lesson_nb = lesson_nb,
                note_number = note_number,
                note = note
            )
            session.add(entry)
        session.commit()

def get_note(level, lesson_nb, note_number):
    stmt = select(GrammarNote).where(
        and_(
            GrammarNote.level == level,
            GrammarNote.lesson_nb == lesson_nb,
            GrammarNote.note_number == note_number
        )
    )
    with Session(engine) as session:
        entry = session.scalars(stmt).one()
        if entry:   
            return str(note_number) + '       ' + entry.note
        else:
            return None
