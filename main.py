from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from app.core.database import engine, Base
from app.api.routes import books, notes, chat
from app.core.session import generate_session_id

import app.models.user
import app.models.book
import app.models.note
import app.models.chat_session
import app.models.message
import app.models.BookIndex

app = FastAPI(title="PDF Notes AI")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

app.include_router(books.router)
app.include_router(notes.router)
app.include_router(chat.router)

@app.get("/")
def root(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = generate_session_id()
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=60 * 60 * 24 * 365,  # 1 year
            httponly=True
        )
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/session")
def get_session(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = generate_session_id()
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True
        )
    return {"session_id": session_id}