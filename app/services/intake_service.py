"""Process intake forms and generate client assessments."""
import json
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import IntakeForm
from app.models.database import ClientIntakeDB
from app.services.llm_service import get_llm_service
from app.prompts.intake_prompts import (
    INTAKE_ASSESSMENT_SYSTEM,
    INTAKE_ASSESSMENT_USER,
)


class ClientAssessment(BaseModel):
    """Structured assessment output from Claude."""
    strengths_summary: str
    transferable_skills: list[str]
    barrier_impact: str
    readiness_level: str = Field(pattern="^(high|medium|low)$")
    recommended_support: list[str]
    missing_info: list[str]
    industry_recommendations: list[str]


class IntakeService:
    """Service for processing client intake forms."""

    async def process_intake(
        self,
        intake: IntakeForm,
        db: Optional[AsyncSession] = None,
    ) -> ClientAssessment:
        """Process an intake form and return a structured assessment."""

        llm = get_llm_service()

        # Generate assessment via Claude
        user_prompt = INTAKE_ASSESSMENT_USER.format(
            intake_json=json.dumps(intake.model_dump(), default=str)
        )

        assessment = await llm.generate_structured(
            system_prompt=INTAKE_ASSESSMENT_SYSTEM,
            user_prompt=user_prompt,
            response_model=ClientAssessment,
            temperature=0.3,
            max_tokens=1500,
        )

        # Persist to database if session provided
        if db:
            await self._save_intake(intake, db)

        return assessment

    async def _save_intake(
        self,
        intake: IntakeForm,
        db: AsyncSession,
    ) -> None:
        """Save intake form to database."""
        db_record = ClientIntakeDB(
            client_id=intake.client_id,
            name=intake.name,
            age=intake.age,
            education_level=intake.education_level.value,
            work_status=intake.work_status.value,
            skills=intake.skills,
            years_experience=intake.years_experience,
            industries_worked=intake.industries_worked,
            certifications=intake.certifications,
            barriers=[b.value for b in intake.barriers],
            support_services=intake.support_services,
            desired_hours=intake.desired_hours,
            willing_to_relocate=intake.willing_to_relocate,
            max_commute_minutes=intake.max_commute_minutes,
            preferred_industries=intake.preferred_industries,
            personal_statement=intake.personal_statement,
            created_at=datetime.utcnow(),
        )
        db.add(db_record)
        await db.commit()

    async def get_client(self, client_id: str, db: AsyncSession) -> Optional[ClientIntakeDB]:
        """Retrieve a client by ID."""
        result = await db.execute(
            select(ClientIntakeDB).where(ClientIntakeDB.client_id == client_id)
        )
        return result.scalar_one_or_none()


# Singleton
_intake_service: Optional[IntakeService] = None

def get_intake_service() -> IntakeService:
    global _intake_service
    if _intake_service is None:
        _intake_service = IntakeService()
    return _intake_service
