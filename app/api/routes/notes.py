from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.note import Note
from app.schemas.note_schema import NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("/{book_id}", response_model=list[NoteResponse])
def get_notes(book_id: int, db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.book_id == book_id).all()
    return notes