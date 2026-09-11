import json
from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

SYSTEM_PROMPT = """You are an onboarding assistant. Given a job description
and a summary of the hired candidate's skills and background, generate a
personalized onboarding plan.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "welcome_message": string,
  "first_day_agenda": [string, ...],
  "access_checklist": [string, ...],
  "checklist": [string, ...]
}

Guidance for each field:
- "first_day_agenda": 4-6 ordered items for the candidate's first day (e.g.
  "9:00 - Welcome meeting with manager", "11:00 - Workstation and tools setup").
- "access_checklist": 4-6 concrete accounts, tools, or hardware to provision
  before or on day one, inferred from the job description when relevant
  (e.g. company email, Slack, GitHub access, laptop, VPN, specific software
  mentioned in the job description).
- "checklist": 5-7 concrete first-two-weeks action items, ordered by priority.
  Include one explicit item about coordinating with the technical
  recruiter/tech lead to assign the candidate a mentor — this is an
  administrative follow-up task for HR, not a technical decision HR makes
  itself.
- Where relevant, note anything specific to this candidate's background (a
  skill gap worth an early focus, or a strength worth leveraging early) in
  the checklist items themselves."""


def _checkable(items: list) -> list[dict]:
    return [{"text": item, "done": False} for item in items if isinstance(item, str)]


def generate_onboarding_checklist(job_title: str, job_description: str, candidate_skills: list, screening_justification: str) -> dict:
    user_prompt = f"""JOB TITLE: {job_title}
JOB DESCRIPTION: {job_description}

HIRED CANDIDATE'S SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Not specified'}
SCREENING NOTES: {screening_justification}"""

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=800)

    try:
        result = _extract_json(raw_response)
    except (json.JSONDecodeError, TypeError):
        if not raw_response:
            retry_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=800)
        else:
            fix_prompt = f"""Your previous response was not a clean JSON object. Here it is:
{raw_response}

Return ONLY the corrected, valid JSON object in the exact shape requested. No markdown
fences, no reasoning, no text before or after it. Start with {{ and end with }}."""
            retry_response = call_llm(SYSTEM_PROMPT, fix_prompt, max_tokens=800)

        try:
            result = _extract_json(retry_response)
        except (json.JSONDecodeError, TypeError):
            return {
                "welcome_message": "Welcome to the team!",
                "first_day_agenda": [],
                "access_checklist": [],
                "checklist": _checkable(["Could not generate a personalized checklist. Please create one manually."]),
            }

    return {
        "welcome_message": result.get("welcome_message", "Welcome to the team!"),
        "first_day_agenda": result.get("first_day_agenda", []) or [],
        "access_checklist": _checkable(result.get("access_checklist", [])),
        "checklist": _checkable(result.get("checklist", [])),
    }