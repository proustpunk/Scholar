from fastapi import Header,APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.session import get_or_create_user
from app.models.book import Book
from app.models.BookIndex import BookIndex
from app.schemas.book_schema import BookResponse, BookIndexCreate, BookIndexResponse
from app.services.notes_service import process_chapter
from app.schemas.note_schema import NoteResponse
import shutil
import os

router = APIRouter(prefix="/books", tags=["books"])

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session found. Please refresh the page.")
    return get_or_create_user(session_id, db)

@router.post("/upload", response_model=BookResponse)
async def upload_book(
    request: Request,
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    book = Book(owner_id=user.id, title=title, file_path=file_path)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@router.get("/", response_model=list[BookResponse])
def get_books(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return db.query(Book).filter(Book.owner_id == user.id).all()

@router.post("/{book_id}/index", response_model=BookIndexResponse)
def add_index_entry(book_id: int, payload: BookIndexCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    book = db.query(Book).filter(Book.id == book_id, Book.owner_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    entry = BookIndex(
        book_id=book_id,
        chapter_name=payload.chapter_name,
        start_page=payload.start_page,
        end_page=payload.end_page
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get("/{book_id}/index", response_model=list[BookIndexResponse])
def get_index(book_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    book = db.query(Book).filter(Book.id == book_id, Book.owner_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return db.query(BookIndex).filter(BookIndex.book_id == book_id).all()

@router.post("/{book_id}/process", response_model=NoteResponse)
def process_book_chapter(book_id: int, chapter_name: str, request: Request, db: Session = Depends(get_db), x_groq_api_key: str = Header(...)):
    user = get_current_user(request, db)
    book = db.query(Book).filter(Book.id == book_id, Book.owner_id == user.id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        note = process_chapter(book_id, chapter_name, book.file_path, db, api_key=x_groq_api_key)
        return note
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")