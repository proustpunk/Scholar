from pydantic import BaseModel
from datetime import datetime
from typing import List

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}

class ChatSessionCreate(BaseModel):
    title: str | None = None

class ChatSessionResponse(BaseModel):
    id: int
    book_id: int
    title: str | None
    created_at: datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}