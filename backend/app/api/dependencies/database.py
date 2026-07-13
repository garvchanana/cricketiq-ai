from typing import Generator
 
from sqlalchemy.orm import Session
 
from app.database.session import SessionLocal
 
 
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.
 
    Usage in route:
        @router.get("/ask")
        def ask(db: Session = Depends(get_db)):
            ...
 
    Guarantees the session is always closed after the request,
    even if an exception is raised during handling.
    """
 
    db = SessionLocal()
 
    try:
        yield db
    finally:
        db.close()