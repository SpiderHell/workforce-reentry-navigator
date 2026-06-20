"""SQLAlchemy async database setup for SQLite."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, JSON
from datetime import datetime
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class ClientIntakeDB(Base):
    __tablename__ = "client_intakes"

    client_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    education_level = Column(String)
    work_status = Column(String)
    skills = Column(JSON, default=list)
    years_experience = Column(Float)
    industries_worked = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    barriers = Column(JSON, default=list)
    support_services = Column(JSON, default=list)
    desired_hours = Column(String)
    willing_to_relocate = Column(Boolean)
    max_commute_minutes = Column(Integer)
    preferred_industries = Column(JSON, default=list)
    personal_statement = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)


class JobOpeningDB(Base):
    __tablename__ = "job_openings"

    job_id = Column(String, primary_key=True)
    employer_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    education_required = Column(String)
    experience_years = Column(Float)
    industry = Column(String)
    location = Column(String)
    remote_option = Column(Boolean, default=False)
    hourly_wage = Column(Float)
    benefits = Column(JSON, default=list)
    barriers_friendly = Column(JSON, default=list)
    training_provided = Column(Boolean, default=False)
    felony_friendly = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    posted_at = Column(DateTime, default=datetime.utcnow)


class JobMatchDB(Base):
    __tablename__ = "job_matches"

    match_id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    job_id = Column(String, nullable=False)
    overall_score = Column(Float)
    skill_score = Column(Float)
    barrier_score = Column(Float)
    preference_score = Column(Float)
    explanation = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)


class CoverLetterDB(Base):
    __tablename__ = "cover_letters"

    draft_id = Column(String, primary_key=True)
    match_id = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    job_id = Column(String, nullable=False)
    content = Column(Text)
    highlights = Column(JSON, default=list)
    tone = Column(String, default="warm")
    generated_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(String, nullable=True)
    approved = Column(Boolean, default=False)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session
