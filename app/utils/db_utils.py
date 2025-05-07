from contextlib import contextmanager
from sqlalchemy.orm import Session

@contextmanager
def safe_db_transaction(db: Session):
    """
    Context manager for safely performing database transactions
    with automatic rollback on error
    """
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e