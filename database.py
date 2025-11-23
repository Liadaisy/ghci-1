# database.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, JSON, Float, Boolean, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum
from datetime import datetime
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///fairfin.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class LoanStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    withdrawn = "withdrawn"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    auth0_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(String, default="user", nullable=False)  # 'user', 'analyst', 'admin'

    loans = relationship("LoanApplication", back_populates="user", cascade="all, delete-orphan")
    auditlogs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    edit_requests = relationship("EditRequest", back_populates="user", cascade="all, delete-orphan")


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    application_data = Column(JSON)
    decision = Column(String, nullable=True)
    status = Column(SAEnum(LoanStatus), default=LoanStatus.pending)
    explanation = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="loans")
    edit_requests = relationship("EditRequest", back_populates="loan", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="auditlogs")


class EditRequest(Base):
    __tablename__ = "edit_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loan_application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    new_monthly_expenses = Column(Float, nullable=True)
    new_existing_loans = Column(Integer, nullable=True)
    new_loan_tenure = Column(Integer, nullable=True)
    withdraw_requested = Column(Boolean, default=False)
    status = Column(String, default="pending")  # 'pending', 'approved', 'rejected'
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="edit_requests")
    loan = relationship("LoanApplication", back_populates="edit_requests")


# Create tables if they don't exist yet
Base.metadata.create_all(bind=engine)
