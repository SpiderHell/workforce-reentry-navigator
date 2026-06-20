"""LangGraph-based intake-to-match-to-cover-letter workflow."""
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import IntakeForm, JobMatch, CoverLetterDraft, JobOpening
from app.services.intake_service import get_intake_service, ClientAssessment
from app.services.job_service import get_job_service
from app.services.cover_letter_service import get_cover_letter_service


class WorkflowState(TypedDict):
    """Shared state across the LangGraph workflow."""
    # Input
    intake: IntakeForm
    db: AsyncSession

    # Intermediate
    assessment: ClientAssessment | None
    matches: List[JobMatch]
    selected_match: JobMatch | None

    # Output
    cover_letter: CoverLetterDraft | None
    plain_english_summary: str | None

    # Error handling
    error: str | None


async def assess_intake_node(state: WorkflowState) -> dict:
    """Node 1: Process intake and generate client assessment."""
    try:
        service = get_intake_service()
        assessment = await service.process_intake(state["intake"], state["db"])
        return {"assessment": assessment, "error": None}
    except Exception as e:
        return {"error": f"Assessment failed: {str(e)}"}


async def match_jobs_node(state: WorkflowState) -> dict:
    """Node 2: Find and score job matches."""
    if state.get("error"):
        return {}

    try:
        service = get_job_service()
        matches = await service.find_matches(
            state["assessment"],
            state["intake"],
            state["db"],
        )

        # Generate plain-English explanations for each match
        for match in matches:
            # Get job details for explanation
            from sqlalchemy import select
            from app.models.database import JobOpeningDB
            result = await state["db"].execute(
                select(JobOpeningDB).where(JobOpeningDB.job_id == match.job_id)
            )
            job = result.scalar_one_or_none()

            if job:
                plain_english = await service.generate_plain_english(
                    match,
                    state["intake"].name,
                    job.title,
                    job.employer_name,
                )
                # Append to explanation
                match.explanation = f"{match.explanation}

📋 FOR CASEWORKERS: {plain_english}"

        # Save matches
        await service.save_matches(matches, state["db"])

        return {"matches": matches, "selected_match": matches[0] if matches else None}
    except Exception as e:
        return {"error": f"Job matching failed: {str(e)}"}


async def generate_cover_letter_node(state: WorkflowState) -> dict:
    """Node 3: Generate cover letter for top match."""
    if state.get("error") or not state.get("selected_match"):
        return {}

    try:
        service = get_cover_letter_service()

        # Get job details
        from sqlalchemy import select
        from app.models.database import JobOpeningDB
        result = await state["db"].execute(
            select(JobOpeningDB).where(JobOpeningDB.job_id == state["selected_match"].job_id)
        )
        job_db = result.scalar_one_or_none()

        if not job_db:
            return {"error": "Job not found for cover letter generation"}

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
            barriers_friendly=[],
            training_provided=job_db.training_provided,
            felony_friendly=job_db.felony_friendly,
        )

        draft = await service.generate_draft(
            state["intake"],
            job,
            state["selected_match"].match_id,
        )

        await service.save_draft(draft, state["db"])

        return {"cover_letter": draft}
    except Exception as e:
        return {"error": f"Cover letter generation failed: {str(e)}"}


def route_after_assessment(state: WorkflowState) -> str:
    """Conditional edge: proceed or end on error."""
    if state.get("error"):
        return "error"
    return "match_jobs"


def route_after_match(state: WorkflowState) -> str:
    """Conditional edge: generate cover letter or end if no matches."""
    if state.get("error"):
        return "error"
    if not state.get("selected_match"):
        return "no_matches"
    return "generate_cover_letter"


# Build the graph
workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("assess_intake", assess_intake_node)
workflow.add_node("match_jobs", match_jobs_node)
workflow.add_node("generate_cover_letter", generate_cover_letter_node)

# Add edges
workflow.set_entry_point("assess_intake")
workflow.add_conditional_edges(
    "assess_intake",
    route_after_assessment,
    {
        "match_jobs": "match_jobs",
        "error": END,
    },
)
workflow.add_conditional_edges(
    "match_jobs",
    route_after_match,
    {
        "generate_cover_letter": "generate_cover_letter",
        "no_matches": END,
        "error": END,
    },
)
workflow.add_edge("generate_cover_letter", END)

# Compile
agent_app = workflow.compile()
