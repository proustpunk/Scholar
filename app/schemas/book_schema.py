from pydantic import BaseModel
from datetime import datetime

class BookCreate(BaseModel):
    title: str

class BookResponse(BaseModel):
    id: int
    title: str
    file_path: str
    created_at: datetime

    model_config = {"from_attributes": True}

class BookIndexCreate(BaseModel):
    chapter_name: str
    start_page: int
    end_page: int

class BookIndexResponse(BaseModel):
    id: int
    book_id: int
    chapter_name: str
    start_page: int
    end_page: int

    model_config = {"from_attributes": True}