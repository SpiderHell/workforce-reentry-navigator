"""Job matching service with scoring and explanation generation."""
import json
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import IntakeForm, JobOpening, JobMatch, BarrierType
from app.models.database import JobOpeningDB, JobMatchDB
from app.services.llm_service import get_llm_service
from app.services.intake_service import ClientAssessment
from app.prompts.intake_prompts import (
    JOB_MATCH_SYSTEM,
    JOB_MATCH_USER,
    EXPLANATION_SYSTEM,
    EXPLANATION_USER,
)
from app.config import get_settings

settings = get_settings()


class MatchScores(BaseModel):
    """Structured match scores from Claude."""
    skill_score: float = Field(ge=0.0, le=1.0)
    barrier_score: float = Field(ge=0.0, le=1.0)
    preference_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    explanation: str
    key_fit_factors: List[str]
    concerns: List[str]


class PlainEnglishExplanation(BaseModel):
    """Human-readable match explanation."""
    summary: str


class JobService:
    """Service for job matching and explanation generation."""

    def __init__(self):
        self.llm = get_llm_service()

    async def find_matches(
        self,
        client_assessment: ClientAssessment,
        intake: IntakeForm,
        db: AsyncSession,
        limit: int = None,
    ) -> List[JobMatch]:
        """Find and score job matches for a client."""
        if limit is None:
            limit = settings.max_matches

        # Get active job openings
        result = await db.execute(
            select(JobOpeningDB).where(JobOpeningDB.is_active == True)
        )
        jobs = result.scalars().all()

        matches = []
        for job_db in jobs:
            job = JobOpening(
                job_id=job_db.job_id,
                employer_name=job_db.employer_name,
                title=job_db.title,
                description=job_db.description,
                required_skills=job_db.required_skills,
                preferred_skills=job_db.preferred_skills or [],
                education_required=job_db.education_required,
                experience_years=job_db.experience_years or 0.0,
                industry=job_db.industry,
                location=job_db.location,
                remote_option=job_db.remote_option,
                hourly_wage=job_db.hourly_wage,
                benefits=job_db.benefits or [],
                barriers_friendly=[BarrierType(b) for b in (job_db.barriers_friendly or [])],
                training_provided=job_db.training_provided,
                felony_friendly=job_db.felony_friendly,
            )

            scores = await self._score_match(client_assessment, intake, job)

            if scores.overall_score >= settings.min_match_threshold:
                match = JobMatch(
                    match_id=str(uuid.uuid4()),
                    client_id=intake.client_id,
                    job_id=job.job_id,
                    overall_score=round(scores.overall_score, 3),
                    skill_score=round(scores.skill_score, 3),
                    barrier_score=round(scores.barrier_score, 3),
                    preference_score=round(scores.preference_score, 3),
                    explanation=scores.explanation,
                )
                matches.append(match)

        # Sort by overall score descending
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return matches[:limit]

    async def _score_match(
        self,
        client_assessment: ClientAssessment,
        intake: IntakeForm,
        job: JobOpening,
    ) -> MatchScores:
        """Score a single job match using Claude."""

        user_prompt = JOB_MATCH_USER.format(
            client_assessment=json.dumps(client_assessment.model_dump()),
            job_json=json.dumps(job.model_dump(), default=str),
        )

        return await self.llm.generate_structured(
            system_prompt=JOB_MATCH_SYSTEM,
            user_prompt=user_prompt,
            response_model=MatchScores,
            temperature=0.2,
            max_tokens=1200,
        )

    async def generate_plain_english(
        self,
        match: JobMatch,
        client_name: str,
        job_title: str,
        employer_name: str,
    ) -> str:
        """Generate plain-English explanation for non-technical staff."""

        user_prompt = EXPLANATION_USER.format(
            client_name=client_name,
            job_title=job_title,
            employer_name=employer_name,
            overall_score=match.overall_score,
            skill_score=match.skill_score,
            barrier_score=match.barrier_score,
            preference_score=match.preference_score,
            explanation=match.explanation,
            key_fit_factors="; ".join(getattr(match, 'key_fit_factors', [])),
            concerns="; ".join(getattr(match, 'concerns', [])),
        )

        result = await self.llm.generate_structured(
            system_prompt=EXPLANATION_SYSTEM,
            user_prompt=user_prompt,
            response_model=PlainEnglishExplanation,
            temperature=0.4,
            max_tokens=800,
        )
        return result.summary

    async def save_matches(self, matches: List[JobMatch], db: AsyncSession) -> None:
        """Persist matches to database."""
        for match in matches:
            db_match = JobMatchDB(
                match_id=match.match_id,
                client_id=match.client_id,
                job_id=match.job_id,
                overall_score=match.overall_score,
                skill_score=match.skill_score,
                barrier_score=match.barrier_score,
                preference_score=match.preference_score,
                explanation=match.explanation,
            )
            db.add(db_match)
        await db.commit()

    async def add_job(self, job: JobOpening, db: AsyncSession) -> None:
        """Add a new job opening."""
        db_job = JobOpeningDB(
            job_id=job.job_id,
            employer_name=job.employer_name,
            title=job.title,
            description=job.description,
            required_skills=job.required_skills,
            preferred_skills=job.preferred_skills,
            education_required=job.education_required.value,
            experience_years=job.experience_years,
            industry=job.industry,
            location=job.location,
            remote_option=job.remote_option,
            hourly_wage=job.hourly_wage,
            benefits=job.benefits,
            barriers_friendly=[b.value for b in job.barriers_friendly],
            training_provided=job.training_provided,
            felony_friendly=job.felony_friendly,
            is_active=job.is_active,
        )
        db.add(db_job)
        await db.commit()


# Singleton
_job_service: Optional[JobService] = None

def get_job_service() -> JobService:
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
