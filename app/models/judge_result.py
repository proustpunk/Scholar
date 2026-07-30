from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class JudgeResult(Base):
    __tablename__ = "judge_results"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    score = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())