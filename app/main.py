"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import init_db, get_db
from app.models.schemas import IntakeForm, JobOpening
from app.agents.workflow import agent_app, WorkflowState
from app.services.job_service import get_job_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Workforce Re-entry Navigator",
    description="AI Job Coaching Agent for Social Services & NGOs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "workforce-reentry-navigator"}


@app.post("/api/intake", response_model=dict)
async def submit_intake(
    intake: IntakeForm,
    db: AsyncSession = Depends(get_db),
):
    """Submit a client intake form and run the full workflow."""

    # Prepare initial state
    initial_state = WorkflowState(
        intake=intake,
        db=db,
        assessment=None,
        matches=[],
        selected_match=None,
        cover_letter=None,
        plain_english_summary=None,
        error=None,
    )

    # Run the LangGraph workflow
    result = await agent_app.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "client_id": intake.client_id,
        "assessment": result["assessment"].model_dump() if result.get("assessment") else None,
        "matches": [m.model_dump() for m in result.get("matches", [])],
        "top_match": result["selected_match"].model_dump() if result.get("selected_match") else None,
        "cover_letter": {
            "draft_id": result["cover_letter"].draft_id,
            "highlights": result["cover_letter"].highlights,
            "content": result["cover_letter"].content,
        } if result.get("cover_letter") else None,
    }


@app.post("/api/jobs", response_model=dict)
async def add_job(
    job: JobOpening,
    db: AsyncSession = Depends(get_db),
):
    """Add a new job opening."""
    service = get_job_service()
    await service.add_job(job, db)
    return {"status": "created", "job_id": job.job_id}


@app.get("/api/matches/{client_id}", response_model=list)
async def get_client_matches(
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all matches for a client."""
    from sqlalchemy import select
    from app.models.database import JobMatchDB
    result = await db.execute(
        select(JobMatchDB).where(JobMatchDB.client_id == client_id)
    )
    matches = result.scalars().all()
    return [{"match_id": m.match_id, "job_id": m.job_id, "overall_score": m.overall_score, 
             "explanation": m.explanation} for m in matches]


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
