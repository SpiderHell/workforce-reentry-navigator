"""Streamlit zero-code web tool for caseworkers."""
import streamlit as st
import requests
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Workforce Re-entry Navigator",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API endpoint (configurable for local vs deployed)
API_URL = st.secrets.get("API_URL", "http://localhost:8000")

st.title("🤝 Workforce Re-entry Navigator")
st.markdown("**AI Job Coaching Agent** — for Social Services & NGOs")
st.divider()

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["📝 New Client Intake", "🔍 Review Matches", "📄 Cover Letters", "ℹ️ Help"],
)

# Health check
try:
    health = requests.get(f"{API_URL}/health", timeout=5)
    if health.status_code == 200:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.warning("⚠️ API Issue")
except:
    st.sidebar.error("❌ API Offline — Check that backend is running")


def new_intake_page():
    """Page for submitting new client intake."""
    st.header("📝 New Client Intake")
    st.markdown("Enter client information below. The AI will assess, match jobs, and draft a cover letter.")

    with st.form("intake_form"):
        col1, col2 = st.columns(2)

        with col1:
            client_id = st.text_input("Client ID", value=f"CLI-{datetime.now().strftime('%Y%m%d-%H%M')}")
            name = st.text_input("Full Name", placeholder="Jane Doe")
            age = st.number_input("Age", min_value=16, max_value=80, value=30)
            education = st.selectbox(
                "Education Level",
                ["none", "ged", "high_school", "some_college", "associates", "bachelors", "graduate"],
            )
            work_status = st.selectbox(
                "Current Work Status",
                ["unemployed", "part_time", "temporary", "seeking"],
            )

        with col2:
            skills = st.text_area("Skills (comma-separated)", placeholder="cooking, forklift, customer service")
            years_exp = st.number_input("Years of Experience", min_value=0.0, max_value=50.0, value=0.0)
            industries = st.text_area("Industries Worked (comma-separated)", placeholder="food service, warehouse, retail")
            certifications = st.text_area("Certifications (comma-separated)", placeholder="ServSafe, OSHA-10")

        st.subheader("Barriers & Support Needs")
        barriers = st.multiselect(
            "Barriers to Employment",
            ["housing", "transportation", "childcare", "substance_use", "mental_health", 
             "legal", "digital_literacy", "language", "none"],
            default=["none"],
        )
        support = st.multiselect(
            "Support Services Needed",
            ["job_training", "resume_help", "interview_coaching", "transportation_assistance",
             "childcare_referral", "housing_assistance", "mental_health_referral"],
        )

        st.subheader("Job Preferences")
        desired_hours = st.radio("Desired Hours", ["full_time", "part_time", "flexible"])
        max_commute = st.slider("Max Commute (minutes)", 0, 120, 30)
        preferred_industries = st.text_area("Preferred Industries (comma-separated)", placeholder="healthcare, construction, hospitality")

        st.subheader("Personal Statement")
        personal_statement = st.text_area(
            "Client's own words about their goals",
            placeholder="I'm looking for a stable job where I can grow...",
            max_chars=2000,
        )

        submitted = st.form_submit_button("🚀 Submit & Process", use_container_width=True)

    if submitted:
        # Build payload
        payload = {
            "client_id": client_id,
            "name": name,
            "age": int(age),
            "education_level": education,
            "work_status": work_status,
            "skills": [s.strip() for s in skills.split(",") if s.strip()],
            "years_experience": float(years_exp),
            "industries_worked": [i.strip() for i in industries.split(",") if i.strip()],
            "certifications": [c.strip() for c in certifications.split(",") if c.strip()],
            "barriers": barriers,
            "support_services": support,
            "desired_hours": desired_hours,
            "willing_to_relocate": False,
            "max_commute_minutes": int(max_commute),
            "preferred_industries": [p.strip() for p in preferred_industries.split(",") if p.strip()],
            "personal_statement": personal_statement,
        }

        with st.spinner("🤖 AI is analyzing, matching jobs, and drafting cover letter..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/intake",
                    json=payload,
                    timeout=120,
                )

                if response.status_code == 200:
                    result = response.json()
                    display_results(result)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Failed to connect: {str(e)}")


def display_results(result):
    """Display workflow results in organized sections."""

    # Assessment
    if result.get("assessment"):
        st.success("✅ Intake Assessment Complete")
        with st.expander("📊 Client Assessment", expanded=True):
            a = result["assessment"]
            st.markdown(f"**Strengths:** {a['strengths_summary']}")
            st.markdown(f"**Readiness Level:** `{a['readiness_level'].upper()}`")
            st.markdown("**Transferable Skills:**")
            for skill in a.get('transferable_skills', []):
                st.markdown(f"- {skill}")
            st.markdown("**Recommended Support:**")
            for svc in a.get('recommended_support', []):
                st.markdown(f"- {svc}")

    # Matches
    matches = result.get("matches", [])
    if matches:
        st.success(f"✅ Found {len(matches)} Job Matches")

        for i, match in enumerate(matches[:3], 1):
            with st.expander(f"🏢 Match #{i}: Score {match['overall_score']:.0%}", expanded=(i==1)):
                cols = st.columns(4)
                cols[0].metric("Overall", f"{match['overall_score']:.0%}")
                cols[1].metric("Skills", f"{match['skill_score']:.0%}")
                cols[2].metric("Barriers", f"{match['barrier_score']:.0%}")
                cols[3].metric("Preferences", f"{match['preference_score']:.0%}")

                st.markdown("**Explanation:**")
                st.info(match['explanation'])
    else:
        st.warning("No matches found above threshold. Consider broadening search criteria.")

    # Cover Letter
    if result.get("cover_letter"):
        st.success("✅ Cover Letter Draft Generated")
        cl = result["cover_letter"]
        with st.expander("📄 Cover Letter Draft", expanded=True):
            st.markdown("**Highlights:**")
            for h in cl['highlights']:
                st.markdown(f"- {h}")

            st.text_area("Full Draft", value=cl['content'], height=400)
            st.download_button(
                "⬇️ Download as .txt",
                cl['content'],
                file_name=f"cover_letter_{result['client_id']}.txt",
            )


def review_matches_page():
    """Page for reviewing existing matches."""
    st.header("🔍 Review Matches")
    client_id = st.text_input("Enter Client ID to lookup")

    if client_id and st.button("Search"):
        try:
            response = requests.get(f"{API_URL}/api/matches/{client_id}")
            if response.status_code == 200:
                matches = response.json()
                for m in matches:
                    st.json(m)
            else:
                st.error("No matches found")
        except Exception as e:
            st.error(str(e))


def cover_letters_page():
    """Page for managing cover letters."""
    st.header("📄 Cover Letters")
    st.info("Cover letters are generated automatically with each intake. Review and download from the intake results page.")


def help_page():
    """Help and documentation page."""
    st.header("ℹ️ Help & Runbook")

    st.markdown("""
    ### Quick Start for Caseworkers

    1. **New Client Intake**: Fill out the form on the left, click Submit
    2. **Review Results**: The AI generates:
       - Client strengths assessment
       - Job matches with scores
       - Plain-English explanations
       - Cover letter draft
    3. **Download**: Save the cover letter as a .txt file
    4. **Follow Up**: Use the match explanations to guide client conversations

    ### Interpreting Match Scores

    | Score | Meaning |
    |-------|---------|
    | 80-100% | Strong match — prioritize this opportunity |
    | 65-79% | Good match — viable option with some support needed |
    | 50-64% | Marginal — significant barriers or skill gaps |
    | <50% | Poor match — not recommended |

    ### Tips for Best Results

    - Be thorough in the skills section — include informal skills
    - Personal statement helps the AI understand client motivation
    - Update the job database regularly through the API

    ### Need Help?

    Contact the program tech lead or refer to the full runbook in `/docs/RUNBOOK.md`
    """)


# Route to page
if page == "📝 New Client Intake":
    new_intake_page()
elif page == "🔍 Review Matches":
    review_matches_page()
elif page == "📄 Cover Letters":
    cover_letters_page()
elif page == "ℹ️ Help":
    help_page()

# Footer
st.divider()
st.caption("Workforce Re-entry Navigator v1.0 | Built with ❤️ for social services")
