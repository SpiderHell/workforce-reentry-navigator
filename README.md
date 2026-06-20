# 🤝 Workforce Re-entry Navigator

**AI Job Coaching Agent for Social Services & NGOs**

An end-to-end system that cuts job-application prep time by ~65% for re-entry clients by using Claude-powered AI to assess intake forms, match candidates to open roles, and generate personalized cover letter drafts — all through a zero-code web interface.

## What It Does

1. **Intake Assessment** — Parses client background, identifies transferable skills, flags barriers, and assesses job readiness
2. **Smart Job Matching** — Scores candidates against open roles on skills, barrier accommodation, and preference alignment
3. **Cover Letter Generation** — Drafts personalized, honest cover letters that address gaps gracefully
4. **Plain-English Explanations** — Every match includes a human-readable summary for non-technical caseworkers

## Quick Start

```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 3. Seed database
python scripts/seed_jobs.py

# 4. Run backend
cd app
uvicorn main:app --reload --port 8000

# 5. Run frontend (new terminal)
streamlit run streamlit_app.py

# 6. Run evaluation
python tests/eval_harness.py
```

## Project Structure

```
workforce-reentry-navigator/
├── app/
│   ├── config.py                    # Pydantic settings
│   ├── main.py                      # FastAPI app
│   ├── agents/
│   │   └── workflow.py              # LangGraph state machine
│   ├── models/
│   │   ├── schemas.py               # Pydantic models
│   │   └── database.py              # SQLAlchemy + SQLite
│   ├── prompts/
│   │   └── intake_prompts.py        # Claude system prompts
│   ├── services/
│   │   ├── llm_service.py           # Claude API wrapper
│   │   ├── intake_service.py        # Intake processing
│   │   ├── job_service.py           # Job matching + scoring
│   │   └── cover_letter_service.py  # Cover letter generation
│   └── utils/
├── tests/
│   └── eval_harness.py              # 120-question test suite
├── scripts/
│   └── seed_jobs.py                 # Sample job data
├── data/                            # SQLite database
├── docs/
│   ├── RUNBOOK.md                   # Staff documentation
│   └── DEPLOYMENT.md                # Render deployment guide
├── streamlit_app.py                 # Zero-code web UI
├── requirements.txt
├── .env.example
└── .gitignore
```

## Stack

- **Python** — Core language
- **Claude API (Anthropic)** — LLM for assessment, matching, and generation
- **LangChain + LangGraph** — Agent workflow orchestration
- **FastAPI** — REST API backend
- **SQLite + aiosqlite** — Lightweight async database
- **Streamlit** — Zero-code frontend for caseworkers
- **Render** — Cloud deployment

## Evaluation Harness

The 120-question evaluation suite catches hallucinations and out-of-scope responses before go-live. Run with:

```bash
python tests/eval_harness.py
```

Categories tested:
- Intake parsing (30 questions)
- Job matching (40 questions)
- Hallucination detection (30 questions)
- Out-of-scope handling (20 questions)


