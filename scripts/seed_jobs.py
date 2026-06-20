"""Seed the database with sample job openings for testing."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import init_db, AsyncSessionLocal
from app.models.database import JobOpeningDB


async def seed_jobs():
    await init_db()

    async with AsyncSessionLocal() as db:
        jobs = [
            JobOpeningDB(
                job_id="JOB-001",
                employer_name="Second Chance Logistics",
                title="Warehouse Associate",
                description="Entry-level warehouse position. Picking, packing, light forklift. No experience required — we train.",
                required_skills=["lifting", "reliability"],
                preferred_skills=["forklift", "basic_math"],
                education_required="none",
                experience_years=0.0,
                industry="logistics",
                location="Industrial District, 15 min from downtown",
                hourly_wage=18.50,
                benefits=["health", "paid_time_off", "training_tuition"],
                barriers_friendly=["housing", "legal", "transportation"],
                training_provided=True,
                felony_friendly=True,
            ),
            JobOpeningDB(
                job_id="JOB-002",
                employer_name="Community Kitchen Partners",
                title="Line Cook",
                description="Prep and line cooking in fast-casual restaurant. Morning and evening shifts available.",
                required_skills=["cooking", "food_safety"],
                preferred_skills=["knife_skills", "inventory"],
                education_required="none",
                experience_years=0.0,
                industry="food_service",
                location="Downtown",
                hourly_wage=16.00,
                benefits=["meals", "flexible_schedule"],
                barriers_friendly=["housing", "childcare", "language"],
                training_provided=True,
                felony_friendly=True,
            ),
            JobOpeningDB(
                job_id="JOB-003",
                employer_name="GreenBuild Construction",
                title="General Laborer",
                description="Construction site cleanup, material moving, basic tool use. Growth path to skilled trades.",
                required_skills=["physical_stamina", "reliability"],
                preferred_skills=["tool_use", "blueprint_reading"],
                education_required="high_school",
                experience_years=0.0,
                industry="construction",
                location="Various sites, bus-accessible",
                hourly_wage=20.00,
                benefits=["health", "apprenticeship_program"],
                barriers_friendly=["transportation", "legal"],
                training_provided=True,
                felony_friendly=True,
            ),
            JobOpeningDB(
                job_id="JOB-004",
                employer_name="TechForward Call Center",
                title="Customer Service Representative",
                description="Inbound customer support. Remote option available after 90 days. Strong communication skills needed.",
                required_skills=["communication", "computer_basic"],
                preferred_skills=["typing", "conflict_resolution"],
                education_required="high_school",
                experience_years=0.0,
                industry="customer_service",
                location="Remote option available",
                remote_option=True,
                hourly_wage=15.50,
                benefits=["health", "remote_work", "career_growth"],
                barriers_friendly=["childcare", "transportation", "mental_health"],
                training_provided=True,
                felony_friendly=False,
            ),
            JobOpeningDB(
                job_id="JOB-005",
                employer_name="FreshStart Manufacturing",
                title="Assembly Technician",
                description="Light assembly work in clean factory environment. Day shift, consistent hours.",
                required_skills=["attention_to_detail", "hand_dexterity"],
                preferred_skills=["quality_control", "teamwork"],
                education_required="none",
                experience_years=0.0,
                industry="manufacturing",
                location="Northside Industrial Park",
                hourly_wage=17.00,
                benefits=["health", "retirement", "on_site_childcare"],
                barriers_friendly=["childcare", "housing", "language"],
                training_provided=True,
                felony_friendly=True,
            ),
        ]

        for job in jobs:
            db.add(job)

        await db.commit()
        print(f"Seeded {len(jobs)} job openings")


if __name__ == "__main__":
    asyncio.run(seed_jobs())
