import os
import json
import logging
from datetime import datetime
import bcrypt
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="candidate")  # 'candidate' or 'recruiter_admin'
    full_name = Column(String(150), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("AnalysisRecord", back_populates="user", cascade="all, delete-orphan")


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    candidate_name = Column(String(150), default="Anonymous Candidate")
    candidate_email = Column(String(150), default="")
    file_name = Column(String(255), default="")
    file_type = Column(String(50), default="pdf")  # 'pdf' or 'docx'
    job_title = Column(String(255), default="General Role")
    job_description = Column(Text, default="")
    ats_score = Column(Integer, default=0)
    matched_skills = Column(Text, default="[]")  # JSON
    missing_skills = Column(Text, default="[]")  # JSON
    full_analysis = Column(Text, default="{}")   # Full JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")


class CompanyDoc(Base):
    __tablename__ = "company_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(100), default="general")  # 'culture', 'tech_stack', 'handbook', 'job_spec'
    content = Column(Text, nullable=False)
    uploaded_by = Column(String(100), default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)


class MockInterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    candidate_name = Column(String(150), default="Candidate")
    job_title = Column(String(255), default="Software Engineer")
    transcript = Column(Text, default="[]")  # JSON list of Q&A + feedback
    average_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# DATABASE CONNECTION & INITIALIZATION
# ============================================================
def get_db_engine():
    """
    Connect to MySQL if configured, otherwise automatically fall back to SQLite.
    Returns: (engine, engine_type_str, message)
    """
    db_url = os.getenv("DATABASE_URL")
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_db = os.getenv("MYSQL_DATABASE")
    mysql_port = os.getenv("MYSQL_PORT", "3306")

    try:
        import streamlit as st
        db_url = db_url or st.secrets.get("DATABASE_URL")
        mysql_host = mysql_host or st.secrets.get("MYSQL_HOST")
        mysql_user = mysql_user or st.secrets.get("MYSQL_USER")
        mysql_password = mysql_password or st.secrets.get("MYSQL_PASSWORD")
        mysql_db = mysql_db or st.secrets.get("MYSQL_DATABASE")
        mysql_port = mysql_port or st.secrets.get("MYSQL_PORT", "3306")
    except Exception:
        pass

    # If explicit MySQL URL or individual MySQL params are present
    if not db_url and mysql_host and mysql_user and mysql_db:
        pwd_part = f":{mysql_password}" if mysql_password else ""
        db_url = f"mysql+pymysql://{mysql_user}{pwd_part}@{mysql_host}:{mysql_port}/{mysql_db}"

    if db_url and db_url.startswith("mysql"):
        try:
            engine = create_engine(db_url, pool_recycle=3600, pool_pre_ping=True)
            # Test connection
            with engine.connect():
                pass
            return engine, "MySQL", f"Connected to MySQL at {mysql_host or 'configured host'}"
        except Exception as e:
            logger.warning(f"MySQL connection failed ({e}). Falling back to SQLite.")

    # SQLite Fallback (Zero config, always reliable)
    sqlite_path = os.path.abspath("resume_analyzer.db")
    engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    return engine, "SQLite", f"Using local SQLite database ({sqlite_path})"


ENGINE, DB_TYPE, DB_STATUS_MSG = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


def init_db():
    """Create all tables and seed initial default users."""
    Base.metadata.create_all(bind=ENGINE)
    seed_default_users()


def get_db():
    """Context manager or generator for database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


# ============================================================
# PASSWORD HASHING HELPERS
# ============================================================
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def seed_default_users():
    """Seed demo accounts if no users exist."""
    session = SessionLocal()
    try:
        if session.query(User).count() == 0:
            admin = User(
                username="admin",
                email="admin@resumepro.ai",
                password_hash=hash_password("Admin@123"),
                role="recruiter_admin",
                full_name="Talent Acquisition Admin"
            )
            candidate = User(
                username="candidate",
                email="candidate@resumepro.ai",
                password_hash=hash_password("Candidate@123"),
                role="candidate",
                full_name="Alex Morgan"
            )
            session.add_all([admin, candidate])
            session.commit()

            # Seed a sample company culture doc for RAG
            seed_doc = CompanyDoc(
                title="NexusTech Engineering & Culture Handbook",
                doc_type="culture",
                content="""
                NexusTech Engineering Standards and Values:
                1. Core Values: Extreme ownership, high customer empathy, rapid prototyping, and continuous learning.
                2. Tech Stack: Python (FastAPI/Django), Java Spring Boot, TypeScript/React, AWS (Lambda, ECS, S3, RDS), Docker, Kubernetes, MySQL, Redis, and Vector DBs.
                3. Code Quality: Clean architecture, test-driven development, CI/CD with GitHub Actions, high observability and telemetry.
                4. Collaboration: Async-first communication, blameless post-mortems, transparent peer code reviews.
                5. Requirements for Engineers: Strong problem-solving skills, deep understanding of distributed systems, proficiency in database optimization, and willingness to learn Generative AI integration.
                """,
                uploaded_by="System"
            )
            session.add(seed_doc)
            session.commit()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        session.rollback()
    finally:
        session.close()


# ============================================================
# USER & AUTH CRUD
# ============================================================
def create_user(username, email, password, role="candidate", full_name=""):
    session = SessionLocal()
    try:
        existing = session.query(User).filter((User.email == email) | (User.username == username)).first()
        if existing:
            return None, "Username or Email already registered."
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            full_name=full_name.strip()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user, "Success"
    except Exception as e:
        session.rollback()
        return None, str(e)
    finally:
        session.close()


def authenticate_user(email_or_username, password):
    session = SessionLocal()
    try:
        user = session.query(User).filter(
            (User.email == email_or_username.strip().lower()) |
            (User.username == email_or_username.strip())
        ).first()
        if not user:
            return None, "User not found."
        if not verify_password(password, user.password_hash):
            return None, "Incorrect password."
        # Detach user representation
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
        return user_data, "Success"
    finally:
        session.close()


# ============================================================
# ANALYSIS RECORD CRUD
# ============================================================
def save_analysis_record(user_id, candidate_name, candidate_email, file_name, file_type, job_title, job_description, analysis_data):
    session = SessionLocal()
    try:
        record = AnalysisRecord(
            user_id=user_id,
            candidate_name=candidate_name or "Candidate",
            candidate_email=candidate_email or "",
            file_name=file_name or "uploaded_resume",
            file_type=file_type or "pdf",
            job_title=job_title or "Job Role",
            job_description=job_description or "",
            ats_score=int(analysis_data.get("ats_score", 0)),
            matched_skills=json.dumps(analysis_data.get("matched_skills", [])),
            missing_skills=json.dumps(analysis_data.get("missing_skills", [])),
            full_analysis=json.dumps(analysis_data)
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.id
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving analysis record: {e}")
        return None
    finally:
        session.close()


def get_user_analysis_history(user_id=None, limit=50):
    session = SessionLocal()
    try:
        query = session.query(AnalysisRecord)
        if user_id:
            query = query.filter(AnalysisRecord.user_id == user_id)
        records = query.order_by(desc(AnalysisRecord.created_at)).limit(limit).all()
        results = []
        for r in records:
            results.append({
                "id": r.id,
                "user_id": r.user_id,
                "candidate_name": r.candidate_name,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "job_title": r.job_title,
                "ats_score": r.ats_score,
                "matched_skills": json.loads(r.matched_skills or "[]"),
                "missing_skills": json.loads(r.missing_skills or "[]"),
                "full_analysis": json.loads(r.full_analysis or "{}"),
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
            })
        return results
    finally:
        session.close()


def get_all_analyses(limit=200):
    return get_user_analysis_history(user_id=None, limit=limit)


def get_analysis_by_id(record_id):
    session = SessionLocal()
    try:
        r = session.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
        if not r:
            return None
        return {
            "id": r.id,
            "user_id": r.user_id,
            "candidate_name": r.candidate_name,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "job_title": r.job_title,
            "job_description": r.job_description,
            "ats_score": r.ats_score,
            "matched_skills": json.loads(r.matched_skills or "[]"),
            "missing_skills": json.loads(r.missing_skills or "[]"),
            "full_analysis": json.loads(r.full_analysis or "{}"),
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
        }
    finally:
        session.close()


# ============================================================
# COMPANY DOCS CRUD (RAG)
# ============================================================
def add_company_doc(title, doc_type, content, uploaded_by="admin"):
    session = SessionLocal()
    try:
        doc = CompanyDoc(
            title=title.strip(),
            doc_type=doc_type.strip(),
            content=content.strip(),
            uploaded_by=uploaded_by
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc.id
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving company doc: {e}")
        return None
    finally:
        session.close()


def get_company_docs():
    session = SessionLocal()
    try:
        docs = session.query(CompanyDoc).order_by(desc(CompanyDoc.created_at)).all()
        return [
            {
                "id": d.id,
                "title": d.title,
                "doc_type": d.doc_type,
                "content": d.content,
                "uploaded_by": d.uploaded_by,
                "created_at": d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else ""
            }
            for d in docs
        ]
    finally:
        session.close()


def delete_company_doc(doc_id):
    session = SessionLocal()
    try:
        doc = session.query(CompanyDoc).filter(CompanyDoc.id == doc_id).first()
        if doc:
            session.delete(doc)
            session.commit()
            return True
        return False
    finally:
        session.close()
