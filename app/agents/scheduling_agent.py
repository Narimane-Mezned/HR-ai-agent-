
from app.llm_client import call_llm
import json

SYSTEM_PROMPT = """You are a scheduling assistant. Given a candidate's name and
a job title, propose 3 realistic interview time slots for next week (weekdays,
business hours, spaced at least a day apart) and write a short, professional
message HR could send to the candidate.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "proposed_slots": [string, string, string],
  "message": string
}"""


def propose_interview_slots(candidate_name: str, job_title: str) -> dict:
    
    user_prompt = f"Candidate: {candidate_name}\nJob: {job_title}"

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=500)

    try:
        return json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {
            "proposed_slots": [],
            "message": f"Could not generate a scheduling proposal for {candidate_name}. Please schedule manually.",
        }