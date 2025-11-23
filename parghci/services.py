# services.py
from contextlib import contextmanager
from models import SessionLocal, User, LoanApplication, EditRequest, AuditLog, LoanStatus
from sqlalchemy.exc import NoResultFound

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def get_or_create_user(session, auth0_id, name, email):
    user = session.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        user = User(auth0_id=auth0_id, name=name, email=email, role=None)
        session.add(user)
        session.flush()
        session.refresh(user)
    return user

def save_loan(session, user_id, application_data):
    loan = LoanApplication(user_id=user_id, application_data=application_data, status=LoanStatus.pending)
    session.add(loan)
    session.flush()
    session.refresh(loan)
    return loan

def list_user_loans(session, user_id):
    return session.query(LoanApplication).filter(LoanApplication.user_id == user_id).order_by(LoanApplication.created_at.desc()).all()

def list_pending_loans(session):
    return session.query(LoanApplication).filter(LoanApplication.status == LoanStatus.pending).order_by(LoanApplication.created_at.asc()).all()

def create_edit_request(session, **kwargs):
    req = EditRequest(**kwargs)
    session.add(req)
    session.flush()
    session.refresh(req)
    return req

def log_action(session, user_id, action):
    log = AuditLog(user_id=user_id, action=action)
    session.add(log)
