import json
from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

SYSTEM_PROMPT = """You are a recruiting assistant. Given a job description,
write 4 short, specific pre-screening questions a candidate should answer
before formal review. Focus on things a CV often doesn't make clear:
availability, work authorization/eligibility to work on-site at the
company's location, direct experience with the single most important
requirement, and salary expectations if relevant.

Do NOT name or assume any specific country, region, or nationality — the
company's location is unknown to you. Phrase the authorization/location
question generically, e.g. "Are you legally authorized to work on-site
at this company's location, or would you require sponsorship/relocation?"

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "questions": [string, string, string, string]
}"""


def generate_prescreening_questions(job_description: str) -> list[str]:
    raw_response = call_llm(SYSTEM_PROMPT, job_description, max_tokens=400)
    try:
        result = _extract_json(raw_response)
        return result.get("questions", [])
    except (json.JSONDecodeError, TypeError):
        return []