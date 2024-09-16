from typing import List
from typing import Optional
import datetime
import pickle
import pytz
from sqlalchemy import ForeignKey, select, String, and_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

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
    lesson : Mapped[int]
    line : Mapped[int]
    position : Mapped[Optional[int]]
    word_id : Mapped[int] = mapped_column(ForeignKey("word_dict.id"))
    word : Mapped["Word"] = relationship(back_populates="index_ref_entries")
    def __repr__(self) -> str:
        return f"IndexEntry(id={self.id!r}, word={self.word!r}, word_id={self.word_id}, lesson={self.lesson!r}, line={self.line!r}), position={self.position!r}"
        
class Sentence(Base):
    __tablename__ = "sentences"
    id: Mapped[int] = mapped_column(primary_key=True)
    sentence: Mapped[str] 
    comment: Mapped[Optional[str]]
    lesson : Mapped[int]
    line : Mapped[int]
    def __repr__(self) -> str:
        return f"Sentence(id={self.id!r}, lesson={self.lesson!r}, line={self.line!r}, sentence ={self.sentence!r}, comment={self.comment!r})"

class LessonSession(Base):
    __tablename__ = "lesson_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped["User"] = relationship(back_populates="sessions")
    lesson: Mapped[int]
    date_time: Mapped[datetime.datetime]
    errors_number: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    errored_sentences : Mapped[List["MarkedSentence"]] = relationship(
        back_populates="session", cascade="all, delete-orphan")
    def __repr__(self) -> str:
        return f"date time : {self.date_time!r}, lesson {self.lesson!r} errors number : {self.errors_number!r}"

class MarkedSentence(Base):
    __tablename__ = "marked_sentences"
    id: Mapped[int] = mapped_column(primary_key=True)
    sentence: Mapped[str] 
    comment: Mapped[Optional[str]]
    line : Mapped[int]
    session_id : Mapped[int] = mapped_column(ForeignKey("lesson_sessions.id"))
    session : Mapped["LessonSession"] = relationship(back_populates="errored_sentences")
    def __repr__(self) -> str:
        return f"Sentence(id={self.id!r}, line={self.line!r}, sentence ={self.sentence!r}, comment={self.comment!r})"

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

def get_database_engine(name, echo=True):
    engine = create_engine(name, echo = echo)   
    Base.metadata.create_all(engine) 
    return engine

database_name = 'sqlite:///db/assimil_spanish.db'
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

def fill_sentences_table(lesson, sentences):
    with Session(engine) as session:
        for line, sentence in enumerate(sentences):
            s_obj = Sentence(
                lesson = lesson,
                line = line,
                sentence = sentence
            )
            session.add(s_obj)
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

def store_lesson_errors(username, lesson_number, errored_sentences, date_time = None):
    if not date_time:
       date_time = datetime.datetime.now()
    with Session(engine) as session:
        stmt = select(User).where(User.username == username)
        user = session.scalars(stmt).one()
        errored_sentences_list = []
        for line in errored_sentences:
            print("----", line, "------")
            errored_sentences_list.append(MarkedSentence(
                line = line,
                sentence = errored_sentences[line]
            ))
        l_obj = LessonSession(
            user = user,
            lesson = lesson_number,
            date_time = date_time,
            errors_number = len(errored_sentences_list),
            errored_sentences = errored_sentences_list
        )
        session.add(l_obj)
        session.commit()


def get_single_lesson_errors(lesson_nb, date_time : datetime.datetime):
    print(f"----- In get_single_lesson_errors  date : {date_time}, of type {type(date_time)}")
    stmt = select(LessonSession).where(
                LessonSession.lesson == lesson_nb,
                LessonSession.date_time == date_time
            )

    errors = {}
    with Session(engine) as session:
        for lesson_session in session.scalars(stmt):
            for sentence_entry in lesson_session.errored_sentences:
                errors[sentence_entry.line] = sentence_entry.sentence

    return errors
   
def get_errors(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None):
    if not begin_date: begin_date = datetime.datetime.min
    if not end_date: end_date = datetime.datetime.max
    stmt = select(MarkedSentence).where(
                    and_(
                        MarkedSentence.date_time >= begin_date,
                        MarkedSentence.date_time <= end_date,
                        MarkedSentence.lesson >= begin_lesson,
                        MarkedSentence.lesson <= end_lesson,
                    )
                )
    errors = []
    with Session(engine) as session:
        for entry in session.scalars(stmt):
            errors.append(entry.sentence)
    return errors

def get_lesson_sessions_history(begin_lesson = 1, end_lesson = 100, begin_date = None, end_date = None):
    print(f"----------------- begin_date : {begin_date}")
    print(f"----------------- end_date : {end_date}")
    if not begin_date: begin_date = datetime.datetime.min
    if not end_date: end_date = datetime.datetime.max
    sessions = {}
    stmt = select(LessonSession).where(
                and_(
                    LessonSession.date_time >= begin_date,
                    LessonSession.date_time <= end_date,
                    LessonSession.lesson <= end_lesson,
                    LessonSession.lesson >= begin_lesson
                )
            )
    with Session(engine) as session:
        for entry in session.scalars(stmt):
            if entry.lesson in sessions:
                sessions[entry.lesson][entry.date_time] = entry.errors_number
            else:
                sessions[entry.lesson] = {entry.date_time : entry.errors_number}
    return sessions
