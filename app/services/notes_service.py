from sqlalchemy.orm import Session
from app.models.note import Note
from app.models.BookIndex import BookIndex
from app.services.pdf_service import extract_pages_as_images, ocr_images, clean_text, chunk_text
from app.services.llm_service import generate_notes
from app.services.rag_service import store_chunks

def process_chapter(book_id: int, chapter_name: str, file_path: str, db: Session, api_key: str) -> Note:
    """Full pipeline: slice → OCR → chunk → notes → store."""

    # Get page range from index
    index_entry = db.query(BookIndex).filter(
        BookIndex.book_id == book_id,
        BookIndex.chapter_name.ilike(chapter_name.strip())
    ).first()

    if not index_entry:
        raise ValueError(f"Chapter '{chapter_name}' not found in book index")

    # Pipeline
    images = extract_pages_as_images(file_path, index_entry.start_page, index_entry.end_page)
    raw_text = ocr_images(images)
    clean = clean_text(raw_text)
    chunks = chunk_text(clean)

    # Store in ChromaDB for RAG
    store_chunks(book_id, chapter_name, chunks)

    # Generate notes via LLM
    notes_content = generate_notes(chunks, api_key=api_key)

    # Save to DB
    note = Note(book_id=book_id, chapter_name=chapter_name, content=notes_content)

    db.add(note)
    db.commit()
    db.refresh(note)

    return note