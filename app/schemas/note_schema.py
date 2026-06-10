from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NoteResponse(BaseModel):
    id: int
    book_id: int
    chapter_name: Optional[str] = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}