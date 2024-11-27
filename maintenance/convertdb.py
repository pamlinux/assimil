import databaseold as db_old
import maintenance.database as db_new

from sqlalchemy.orm import Session
from sqlalchemy import select, and_


print(f"Conviert FROM database : {db_old} TO database : {db_new}")

print("Old engine : ", db_old.engine)
print("New engine : ", db_new.engine)

def copy_user():
    with Session(db_old.engine) as old_session:
        with Session(db_new.engine) as new_session:
            stmt = select(db_old.User)
            for entry in old_session.scalars(stmt):
                user = db_new.User(
                    username = entry.username,
                    password = entry.password,
                    fullname = entry.fullname,
                    email = entry.email,
                    parameters = entry.parameters,
                    parameters_version = entry.parameters_version,
                )
                new_session.add(user)
            new_session.commit()



def copy_paragraphs():
    with Session(db_old.engine) as old_session:
        with Session(db_new.engine) as new_session:
            stmt = select(db_old.Paragraph)
            for entry in old_session.scalars(stmt):
                para = db_new.Paragraph(
                    level = 0,
                    section = entry.section,
                    lesson_nb = entry.lesson_nb,
                    line_nb = entry.line_nb,
                    paragraph = entry.paragraph,
                    translation = entry.translation,
                    has_dash_dialogue = entry.has_dash_dialogue,
                    grammar_indexes = entry.grammar_indexes,
                    data = entry.data
                )
                new_session.add(para)
            new_session.commit()

def copy_lesson_sessions():
    stmt_old_lesson_session = select(db_old.LessonSession)
    new_session = Session(db_new.engine) 
    stmt_new_user = select(db_new.User).where(db_new.User.username == "pam")
    pam = new_session.scalars(stmt_new_user).one()
    print(pam)
    with Session(db_old.engine) as session_old:
        for entry in session_old.scalars(stmt_old_lesson_session):
            #print(entry.id)
            lesson_session = db_new.LessonSession(
                user=pam,
                level = 0,
                lesson_nb = entry.lesson,
                date_time = entry.date_time,
                errors_number = entry.errors_number,
                errored_paragraphs = []
            )
            for ep in entry.errored_paragraphs:
                errored_paragraph = db_new.MarkedParagraph(
                    paragraph = ep.paragraph,
                    comment = ep.comment,
                    line_nb = ep.line,
                    session = lesson_session
                )
                lesson_session.errored_paragraphs.append(errored_paragraph)
            new_session.add(lesson_session)
        new_session.commit()

def copy_grammar_notes():
    stmt_old = select(db_old.GrammarNote)
    new_session = Session(db_new.engine)
    with Session(db_old.engine) as session_old:
        for entry in session_old.scalars(stmt_old):
            grammar_note = db_new.GrammarNote(
                level = 0,
                lesson_nb = entry.lesson,
                note_number = entry.note_number,
                note = entry.note
            )
            new_session.add(grammar_note)
        new_session.commit()


def convert():
    copy_user()
    copy_paragraphs()
    copy_lesson_sessions()
    copy_grammar_notes()
