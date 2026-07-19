from datetime import date
from app.llm_client import call_llm
import json

SYSTEM_PROMPT = """You are a scheduling assistant. Given a candidate's name, a
job title, and today's actual date, propose 3 realistic interview time slots
for the upcoming week (weekdays, business hours, spaced at least a day apart,
all AFTER today's date) and write a short, professional message HR could send
to the candidate.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "proposed_slots": [string, string, string],
  "message": string
}"""


def propose_interview_slots(candidate_name: str, job_title: str) -> dict:
    today_str = date.today().strftime("%A, %B %d, %Y")
    user_prompt = f"Today's date: {today_str}\nCandidate: {candidate_name}\nJob: {job_title}"

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=500)

    try:
        return json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {
            "proposed_slots": [],
            "message": f"Could not generate a scheduling proposal for {candidate_name}. Please schedule manually.",
        }
    
def build_confirmation_message(candidate_name: str, job_title: str, confirmed_time: str) -> str:
    
    return (
        f"Dear {candidate_name},\n\n"
        f"We're pleased to confirm your interview for the {job_title} position "
        f"on {confirmed_time}.\n\n"
        f"We look forward to speaking with you.\n\n"
        f"Best regards"
    )