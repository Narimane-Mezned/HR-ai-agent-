import json
from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

EMAIL_PROMPTS = {
    "preselection_refuse": """You are an HR communication assistant writing a preliminary
screening rejection email. The candidate applied for a position but was not selected to
move forward to the interview stage. Be warm, respectful, and professional. Do not give
specific reasons for the decision. Keep it concise (under 120 words).""",
    "preselection_accept": """You are an HR communication assistant writing an email letting
a candidate know they have passed the initial screening stage and will be invited to an
interview. Be warm and encouraging. Explicitly say the interview time will be shared soon
in a separate message. Keep it concise (under 120 words).""",
    "total_refuse": """You are an HR communication assistant writing a rejection email to a
candidate after they completed an interview. Be warm, respectful, and professional. Thank
them for their time interviewing. Do not give specific reasons for the decision. Keep it
concise (under 130 words).""",
    "total_accept": """You are an HR communication assistant writing a job offer /
acceptance email to a candidate after a successful interview. Be warm and enthusiastic.
Say the company will follow up soon with next steps (start date, paperwork, etc). Keep it
concise (under 130 words).""",
}

COMMON_INSTRUCTIONS = """
Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "subject": string,
  "body": string
}
Format the body as clear, readable paragraphs separated by blank lines — a short
greeting line, then 1-2 short paragraphs, then the sign-off, each on its own line
group. Sign off as "The [Company Name] HR Team" (using the company name provided
below), not as an individual person's name. Do not use bracketed placeholders."""


def _fallback_email(action: str, candidate_name: str, job_title: str, company_name: str) -> dict:
    hr_signature = f"The {company_name} HR Team" if company_name else "The HR Team"
    sign_off = f"\n\nBest regards,\n{hr_signature}"
    templates = {
        "preselection_refuse": (
            f"Update on your application — {job_title}",
            f"Dear {candidate_name},\n\n"
            f"Thank you for your interest in the {job_title} position. "
            f"After careful review, we will not be moving forward with your application at this time.\n\n"
            f"We wish you the best in your job search.{sign_off}",
        ),
        "preselection_accept": (
            f"You're moving forward — {job_title}",
            f"Dear {candidate_name},\n\n"
            f"We're pleased to let you know you've been selected to move forward to the interview "
            f"stage for the {job_title} position.\n\n"
            f"We will share the interview time with you shortly.{sign_off}",
        ),
        "total_refuse": (
            f"Update on your application — {job_title}",
            f"Dear {candidate_name},\n\n"
            f"Thank you for taking the time to interview for the {job_title} position. "
            f"After careful consideration, we have decided to move forward with another candidate.\n\n"
            f"We wish you the best in your job search.{sign_off}",
        ),
        "total_accept": (
            f"Congratulations — {job_title}",
            f"Dear {candidate_name},\n\n"
            f"Congratulations! We're delighted to offer you the {job_title} position.\n\n"
            f"We will follow up soon with next steps.{sign_off}",
        ),
    }
    subject, body = templates[action]
    return {"subject": subject, "body": body}


def generate_candidate_email(action: str, candidate_name: str, job_title: str, company_name: str) -> dict:
    if action not in EMAIL_PROMPTS:
        raise ValueError(f"Unknown action: {action}")

    system_prompt = EMAIL_PROMPTS[action] + COMMON_INSTRUCTIONS
    user_prompt = (
        f"Candidate name: {candidate_name}\n"
        f"Job title: {job_title}\n"
        f"Company name: {company_name or 'the company'}"
    )

    raw_response = call_llm(system_prompt, user_prompt, max_tokens=400)

    try:
        result = _extract_json(raw_response)
        if result.get("subject") and result.get("body"):
            return {"subject": result["subject"], "body": result["body"]}
    except (json.JSONDecodeError, TypeError):
        pass

    if raw_response:
        fix_prompt = f"""Your previous response was not a clean JSON object. Here it is:
{raw_response}

Return ONLY the corrected, valid JSON object in the exact shape requested. No markdown
fences, no reasoning, no text before or after it. Start with {{ and end with }}."""
        retry_response = call_llm(system_prompt, fix_prompt, max_tokens=400)
        try:
            result = _extract_json(retry_response)
            if result.get("subject") and result.get("body"):
                return {"subject": result["subject"], "body": result["body"]}
        except (json.JSONDecodeError, TypeError):
            pass

    return _fallback_email(action, candidate_name, job_title, company_name)