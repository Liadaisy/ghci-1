# services.py
from contextlib import contextmanager
from typing import List

from models import SessionLocal, AuditLog, LoanApplication, LoanStatus


@contextmanager
def sessionscope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def logaction(session, user_id: int, action: str) -> None:
    log = AuditLog(user_id=user_id, action=action)
    session.add(log)


def listuserloans(session, user_id: int) -> List[LoanApplication]:
    return (
        session.query(LoanApplication)
        .filter(LoanApplication.user_id == user_id)
        .order_by(LoanApplication.created_at.desc())
        .all()
    )


def listpendingloans(session) -> List[LoanApplication]:
    return (
        session.query(LoanApplication)
        .filter(LoanApplication.status == LoanStatus.pending)
        .order_by(LoanApplication.created_at.asc())
        .all()
    )
