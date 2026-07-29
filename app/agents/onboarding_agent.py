import json
from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

SYSTEM_PROMPT = """You are an onboarding assistant. Given a job description
and a summary of the hired candidate's skills and background, generate a
personalized first-two-weeks onboarding checklist: 5-7 concrete action
items, ordered roughly by priority. Where relevant, note anything specific
to this candidate's background (a skill gap worth an early focus, or a
strength worth leveraging early).

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "welcome_message": string,
  "checklist": [string]
}"""


def generate_onboarding_checklist(job_title: str, job_description: str, candidate_skills: list, screening_justification: str) -> dict:
    user_prompt = f"""JOB TITLE: {job_title}
JOB DESCRIPTION: {job_description}

HIRED CANDIDATE'S SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Not specified'}
SCREENING NOTES: {screening_justification}"""

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=700)

    try:
        return _extract_json(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {
            "welcome_message": "Welcome to the team!",
            "checklist": ["Could not generate a personalized checklist. Please create one manually."],
        }