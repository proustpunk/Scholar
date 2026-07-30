from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.models.note import Note
from app.models.BookIndex import BookIndex
from app.services.pdf_service import extract_pages_as_images, ocr_images, clean_text, chunk_text
from app.services.llm_service import generate_notes, judge_note_background
from app.services.rag_service import store_chunks

def process_chapter(book_id: int, chapter_name: str, file_path: str, db: Session, api_key: str, background_tasks: BackgroundTasks) -> Note:
    index_entry = db.query(BookIndex).filter(
        BookIndex.book_id == book_id,
        BookIndex.chapter_name.ilike(chapter_name.strip())
    ).first()

    if not index_entry:
        raise ValueError(f"Chapter '{chapter_name}' not found in book index")

    images = extract_pages_as_images(file_path, index_entry.start_page, index_entry.end_page)
    raw_text = ocr_images(images)
    clean = clean_text(raw_text)
    chunks = chunk_text(clean)

    store_chunks(book_id, chapter_name, chunks)

    combined_text = "\n\n".join(chunks)
    notes_content = generate_notes(chunks, api_key=api_key)

    note = Note(book_id=book_id, chapter_name=chapter_name, content=notes_content)
    db.add(note)
    db.commit()
    db.refresh(note)

    background_tasks.add_task(judge_note_background, note.id, combined_text, notes_content)

    return note