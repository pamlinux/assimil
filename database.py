from typing import List
from typing import Optional
import re
import datetime
import pickle
import pytz
from pydantic import BaseModel
from sqlalchemy import ForeignKey, select, String, and_, desc, exc, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from paths import get_path
import yaml

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
    
class Media(Base):
    __tablename__ = 'media'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    media_type: Mapped[str] # "movie" or "series"
    season: Mapped[Optional[int]]
    series_number: Mapped[Optional[int]] # Number of the series
    series_title: Mapped[Optional[str]]
    disc_number: Mapped[Optional[int]] # Number of the DVD or Blu-ray
    video_file: Mapped[Optional[str]]
    spanish_subtitles_file: Mapped[Optional[str]]
    french_subtitles_file: Mapped[Optional[str]]
    long_spanish_subtitles_file: Mapped[Optional[str]]
    long_french_subtitles_file: Mapped[Optional[str]]
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


def get_database_engine(name, echo=True):
    engine = create_engine(name, echo = echo)   
    Base.metadata.create_all(engine) 
    return engine

#database_name = "sqlite:////Users/pam/assimil/db/assimil_spanish_mnt3.db"
database_name = get_path('database_name')

global engine
engine = get_database_engine(database_name, False)

def parse_srt_time_range(timestamp: str):
    """
    Converts an SRT timestamp into start_time and end_time.

    Example:
    Input: "00:01:23,456 --> 00:01:25,789"
    Output: (datetime.time(0, 1, 23, 456000), datetime.time(0, 1, 25, 789000))
    """
    pattern = r"(\d{2}):(\d{2}):(\d{2}).(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}).(\d{3})"
    match = re.match(pattern, timestamp)

    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}")

    h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())

    start_time = datetime.time(h1, m1, s1, ms1 * 1000)
    end_time = datetime.time(h2, m2, s2, ms2 * 1000)

    return start_time, end_time

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

    if paragraphs_translation == {}: raise NoSuchLesson
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

def update_subtitle(id: int, languageVariant: str, text: str):
    if languageVariant in ["es", "fr"]:
        subtitle_type = "media"
    elif  languageVariant in ["eslong", "frlong"]:
        subtitle_type = "long"

    stmt = select(Subtitle).where(Subtitle.id == id)
                        
    with Session(engine) as session:
        entry = session.scalars(stmt).one()
        if subtitle_type != entry.subtitle_type:
            raise
        if languageVariant in ["es", "eslong"]:
            entry.spanish_text = text
        elif languageVariant in ["eslong", "frlong"]:
            entry.french_text = text
        else:
            raise
        #print(entry.id, entry.spanish_text, entry.french_text)
        session.commit()

def format_srt_timestamp(start_time: datetime.time, end_time: datetime.time) -> str:
    """Convert two objects datetime.time to one timestamp SRT."""
    return f"{start_time.strftime('%H:%M:%S.%f')[:-3]} --> {end_time.strftime('%H:%M:%S.%f')[:-3]}"

import datetime

def time_to_seconds(time_object: datetime.time) -> float:
    """
    Converts a datetime.time object to the total number of seconds since midnight,
    including microseconds as a fractional part.

    Args:
        time_object: The datetime.time object.

    Returns:
        The total number of seconds as a float.
    """
    total_seconds = (time_object.hour * 3600) + (time_object.minute * 60) + time_object.second + (time_object.microsecond / 1_000_000)
    return total_seconds

def get_es_and_fr_subtitles(subtitle_type: str):
    stmt = select(Subtitle).where(
        Subtitle.subtitle_type == subtitle_type
    )
    
    subtitles = []

    with Session(engine) as session:
        for entry in session.scalars(stmt):
            subtitles.append({
                "id": entry.id,
                "timestamp": format_srt_timestamp(entry.start_time, entry.end_time),
                "spanish": entry.spanish_text,
                "french": entry.french_text
            })

    return subtitles

def get_es_subtitles(subtitle_type: str):
    stmt = select(Subtitle).where(
        Subtitle.subtitle_type == subtitle_type
    )
    
    subtitles = []

    with Session(engine) as session:
        for entry in session.scalars(stmt):
            subtitles.append({
                "id": entry.id,
                "start": time_to_seconds(entry.start_time), 
                "end": time_to_seconds(entry.end_time),
                "text": entry.spanish_text,
            })

    return subtitles

def get_fr_subtitles(subtitle_type: str):
    stmt = select(Subtitle).where(
        Subtitle.subtitle_type == subtitle_type
    )
    
    subtitles = []

    with Session(engine) as session:
        for entry in session.scalars(stmt):
            subtitles.append({
                "id": entry.id,
                "start": time_to_seconds(entry.start_time), 
                "end": time_to_seconds(entry.end_time),
                "text": entry.french_text,
           })

    return subtitles

def update_or_store_media(media: MediaMetadata):
    stmt = select(Media).where(
        and_(
            Media.media_type == media.media_type,
            Media.disc_number == media.disc_number,
            Media.title == media.title,
            Media.series_title == media.series_title,
            Media.series_number == media.series_number,
            Media.season == media.season
        )
    )

    with Session(engine) as session:
        try:
            entry = session.scalars(stmt).one()
            print(f"Media already exists : {entry}")
        except exc.NoResultFound:
            print("Media Does not exists {media}}")
            entry = Media(
                media_type = media.media_type,
                disc_number = media.disc_number,
                title = media.title,
                series_title = media.series_title,
                series_number = media.series_number,
                season = media.season,
                video_file = media.video_file,
                spanish_subtitles_file = media.spanish_subtitles_file,
                long_spanish_subtitles_file = media.long_spanish_subtitles_file,
                french_subtitles_file = media.french_subtitles_file,
                long_french_subtitles_file = media.long_french_subtitles_file
             )
            session.add(entry)
            session.commit()
            print(f"Media Created : {entry}")

def lookup_media(media : MediaMetadata):
    stmt = select(Media).where(
        and_(
            Media.media_type == media.media_type,
            Media.disc_number == media.disc_number,
            Media.title == media.title,
            Media.series_title == media.series_title,
            Media.series_number == media.series_number,
            Media.season == media.season
        )
    )
    
    medias = []

    with Session(engine) as session:
        for entry in session.scalars(stmt):
            media_data = MediaMetadata(
                title = entry.title,
                media_type = entry.media_type,
                disc_number = entry.disc_number,
                season = entry.season,
                series_number = entry.series_number,
                series_title = entry.series_title,
                video_file = entry.video_file,
                spanish_subtitles_file = entry.spanish_subtitles_file,
                long_spanish_subtitles_file = entry.long_spanish_subtitles_file,
                french_subtitles_file = entry.french_subtitles_file,
                long_french_subtitles_file = entry.long_french_subtitles_file
            )
            medias.append(media_data)
    return media_data
   
def store_subtitles(media_metadata: MediaMetadata, subtitle_type: str, es_subtitles: str, fr_subtitles: str):
    stmt = select(Media).where(
        and_(
            Media.title == media_metadata.title,
            Media.disc_number == media_metadata.disc_number,
            Media.media_type == media_metadata.media_type,
            Media.series_title == media_metadata.series_title,
            Media.season == media_metadata.season,
            Media.series_number == media_metadata.series_number
        )
    )

    with Session(engine) as session:
        media = session.scalars(stmt).one()
        print(media.title)
        print(media.id)
        print(media.media_type)
        print(media.series_title)
        print(media.disc_number)
    
        for index, es_subtitle in enumerate(es_subtitles):
            fr_subtitle = fr_subtitles[index]
            start_time, end_time = parse_srt_time_range(es_subtitle['timestamp'])

            print(start_time, end_time, es_subtitle['text'], fr_subtitle['text'])

            entry = Subtitle(
                index = index + 1,
                media = media,
                start_time = start_time,
                end_time = end_time,
                spanish_text = es_subtitle['text'],
                french_text = fr_subtitle['text'],
                subtitle_type = subtitle_type
            )
            session.add(entry)
            
        session.commit()

