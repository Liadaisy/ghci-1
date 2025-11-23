# models.py
import os
import enum
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, JSON, ForeignKey, Enum
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from contextlib import contextmanager
from datetime import datetime

# ----------------------------------------
# DATABASE CONFIG
# ----------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///fairfin.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# ----------------------------------------
# ENUMS
# ----------------------------------------
class LoanStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

# Compatibility alias (important!)
# So `from models import LoanStatus` works
LoanStatus = LoanStatusEnum


# ----------------------------------------
# MODELS
# ----------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    auth0id = Column(String(500), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default="user", nullable=False)

    loans = relationship("LoanApplication", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    application_data = Column(JSON)

    status = Column(
        Enum(LoanStatusEnum),
        default=LoanStatusEnum.pending,
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="loans")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


# ----------------------------------------
# SESSION MANAGER
# ----------------------------------------
@contextmanager
def sessionscope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


# ----------------------------------------
# DATABASE INIT
# ----------------------------------------
def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


# Run only when executed directly
if __name__ == "__main__":
    init_db()
