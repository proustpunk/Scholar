from fastapi import Header,APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.schemas.chat_schema import ChatSessionCreate, ChatSessionResponse, MessageCreate, MessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/session/{book_id}", response_model=ChatSessionResponse)
def create_session(book_id: int, payload: ChatSessionCreate, db: Session = Depends(get_db)):
    session = ChatSession(book_id=book_id, title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.post("/session/{session_id}/message", response_model=MessageResponse)
def add_message(session_id: int, payload: MessageCreate, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = Message(session_id=session_id, role="user", content=payload.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/session/{session_id}", response_model=ChatSessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

from app.services.rag_service import ask_question
@router.post("/ask/{book_id}")
def ask(book_id: int, chapter_name: str, question: str, db: Session = Depends(get_db),x_groq_api_key: str = Header(...)):
    try:
        # Get or create a session for this book+chapter
        session = db.query(ChatSession).filter(
            ChatSession.book_id == book_id,
            ChatSession.title == chapter_name
        ).first()

        if not session:
            session = ChatSession(book_id=book_id, title=chapter_name)
            db.add(session)
            db.commit()
            db.refresh(session)

        # Save user message
        user_msg = Message(session_id=session.id, role="user", content=question)
        db.add(user_msg)
        db.commit()

        # Get answer
        answer = ask_question(book_id, chapter_name, question,api_key=x_groq_api_key)

        # Save assistant message
        assistant_msg = Message(session_id=session.id, role="assistant", content=answer)
        db.add(assistant_msg)
        db.commit()

        return {"question": question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))