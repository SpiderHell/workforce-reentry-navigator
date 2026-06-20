"""Generate personalized cover letter drafts."""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import CoverLetterDraft, IntakeForm, JobOpening
from app.models.database import CoverLetterDB
from app.services.llm_service import get_llm_service
from app.prompts.intake_prompts import COVER_LETTER_SYSTEM, COVER_LETTER_USER


class CoverLetterService:
    """Service for generating cover letter drafts."""

    def __init__(self):
        self.llm = get_llm_service()

    async def generate_draft(
        self,
        intake: IntakeForm,
        job: JobOpening,
        match_id: str,
        tone: str = "warm",
    ) -> CoverLetterDraft:
        """Generate a personalized cover letter draft."""

        # Build experience summary
        exp_summary = f"{intake.years_experience or 0} years of experience"
        if intake.industries_worked:
            exp_summary += f" in {', '.join(intake.industries_worked)}"

        barriers_str = ", ".join([b.value for b in intake.barriers]) if intake.barriers else "none"

        user_prompt = COVER_LETTER_USER.format(
            name=intake.name,
            skills=", ".join(intake.skills),
            experience_summary=exp_summary,
            personal_statement=intake.personal_statement or "Looking for a fresh start and meaningful work.",
            barriers=barriers_str,
            job_title=job.title,
            employer_name=job.employer_name,
            job_description=job.description,
            required_skills=", ".join(job.required_skills),
            tone=tone,
        )

        content = await self.llm.generate_text(
            system_prompt=COVER_LETTER_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.6,
            max_tokens=2000,
        )

        # Extract highlights (simple heuristic - first sentences of paragraphs)
        paragraphs = [p.strip() for p in content.split('

') if p.strip()]
        highlights = []
        for p in paragraphs[:3]:
            sentences = p.split('. ')
            if sentences:
                highlights.append(sentences[0][:100] + '...')

        return CoverLetterDraft(
            draft_id=str(uuid.uuid4()),
            match_id=match_id,
            client_id=intake.client_id,
            job_id=job.job_id,
            content=content.strip(),
            highlights=highlights,
            tone=tone,
        )

    async def save_draft(self, draft: CoverLetterDraft, db: AsyncSession) -> None:
        """Persist cover letter to database."""
        db_draft = CoverLetterDB(
            draft_id=draft.draft_id,
            match_id=draft.match_id,
            client_id=draft.client_id,
            job_id=draft.job_id,
            content=draft.content,
            highlights=draft.highlights,
            tone=draft.tone,
        )
        db.add(db_draft)
        await db.commit()


# Singleton
_cover_letter_service: Optional[CoverLetterService] = None

def get_cover_letter_service() -> CoverLetterService:
    global _cover_letter_service
    if _cover_letter_service is None:
        _cover_letter_service = CoverLetterService()
    return _cover_letter_service
