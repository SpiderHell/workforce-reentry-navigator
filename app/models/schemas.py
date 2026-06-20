"""Pydantic schemas for intake, jobs, matches, and cover letters."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class EducationLevel(str, Enum):
    NONE = "none"
    GED = "ged"
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    GRADUATE = "graduate"


class WorkStatus(str, Enum):
    UNEMPLOYED = "unemployed"
    PART_TIME = "part_time"
    TEMPORARY = "temporary"
    SEEKING = "seeking"


class BarrierType(str, Enum):
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    CHILDCARE = "childcare"
    SUBSTANCE_USE = "substance_use"
    MENTAL_HEALTH = "mental_health"
    LEGAL = "legal"
    DIGITAL_LITERACY = "digital_literacy"
    LANGUAGE = "language"
    NONE = "none"


class IntakeForm(BaseModel):
    """Client intake form capturing background, skills, and barriers."""
    client_id: str = Field(..., description="Unique client identifier")
    name: str
    age: int = Field(..., ge=16, le=80)
    education_level: EducationLevel
    last_employment_date: Optional[str] = None
    work_status: WorkStatus

    # Skills & Experience
    skills: List[str] = Field(default_factory=list, description="e.g., ['cooking', 'forklift', 'customer_service']")
    years_experience: Optional[float] = Field(None, ge=0, le=50)
    industries_worked: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    # Barriers & Support Needs
    barriers: List[BarrierType] = Field(default_factory=list)
    support_services: List[str] = Field(default_factory=list, description="e.g., ['job_training', 'resume_help']")

    # Preferences
    desired_hours: Literal["full_time", "part_time", "flexible"] = "full_time"
    willing_to_relocate: bool = False
    max_commute_minutes: int = 60
    preferred_industries: List[str] = Field(default_factory=list)

    # Narrative
    personal_statement: Optional[str] = Field(None, max_length=2000, description="Client's own words about goals")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class JobOpening(BaseModel):
    """A job opening from partner employers."""
    job_id: str
    employer_name: str
    title: str
    description: str
    required_skills: List[str]
    preferred_skills: List[str] = Field(default_factory=list)
    education_required: EducationLevel = EducationLevel.HIGH_SCHOOL
    experience_years: float = 0.0
    industry: str
    location: str
    remote_option: bool = False
    hourly_wage: Optional[float] = None
    benefits: List[str] = Field(default_factory=list)
    barriers_friendly: List[BarrierType] = Field(default_factory=list, description="Barriers this employer accommodates")
    training_provided: bool = False
    felony_friendly: bool = False
    is_active: bool = True
    posted_at: datetime = Field(default_factory=datetime.utcnow)


class JobMatch(BaseModel):
    """A scored match between a client and a job opening."""
    match_id: str
    client_id: str
    job_id: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    skill_score: float = Field(..., ge=0.0, le=1.0)
    barrier_score: float = Field(..., ge=0.0, le=1.0)
    preference_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str = Field(..., description="Plain-English explanation for caseworkers")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CoverLetterDraft(BaseModel):
    """AI-generated cover letter draft for a specific match."""
    draft_id: str
    match_id: str
    client_id: str
    job_id: str
    content: str = Field(..., max_length=4000)
    highlights: List[str] = Field(default_factory=list, description="Key points the letter emphasizes")
    tone: Literal["formal", "warm", "confident", "humble"] = "warm"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    approved: bool = False


class EvaluationResult(BaseModel):
    """Result from the 120-question evaluation harness."""
    question_id: str
    category: Literal["intake_parsing", "job_matching", "cover_letter", "hallucination", "out_of_scope"]
    input_data: dict
    expected_output: str
    actual_output: str
    passed: bool
    score: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None
