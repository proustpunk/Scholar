import uuid
from sqlalchemy.orm import Session
from app.models.user import User

def get_or_create_user(session_id: str, db: Session) -> User:
    """Find existing user by session_id or create a new one."""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = User(
            name=f"user_{session_id[:8]}",
            session_id=session_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def generate_session_id() -> str:
    return str(uuid.uuid4())