from sqlalchemy.orm import Session

from app.models import Flashcard


def get_flashcards(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Flashcard).offset(skip).limit(limit).all()
