import json
from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

QUESTION_COUNT_BY_LEVEL = {
    "Junior": 3,
    "Mid": 4,
    "Senior": 5,
}
DEFAULT_QUESTION_COUNT = 4


def _build_questions_prompt(question_count: int) -> str:
    return f"""You are a recruiting assistant. Given a job description,
write {question_count} short, specific pre-screening questions a candidate should answer
before formal review. Focus on things a CV often doesn't make clear:
availability, work authorization/eligibility to work on-site at the
company's location, direct experience with the single most important
requirement, and salary expectations if relevant.

Do NOT name or assume any specific country, region, or nationality — the
company's location is unknown to you. Phrase the authorization/location
question generically, e.g. "Are you legally authorized to work on-site
at this company's location, or would you require sponsorship/relocation?"

CRITICAL: Never include bracketed placeholders like "[insert cloud provider]"
or "[insert specific technology]" in a question. Every question must be fully
concrete and ready to show a candidate as-is. If the job description names a
specific technology, tool, or requirement, use that exact term in the
question. If the job description is too generic to name anything specific,
write a general version of the question instead of leaving a placeholder
(e.g. "What tools or technologies have you used for this type of work?"
instead of "...with [insert tool]?").

Return ONLY a JSON object with this exact shape, no text before or after it:
{{
  "questions": [string, ...]  // exactly {question_count} questions
}}"""


def generate_prescreening_questions(job_description: str, experience_level: str = None) -> list[str]:
    question_count = QUESTION_COUNT_BY_LEVEL.get(experience_level, DEFAULT_QUESTION_COUNT)
    system_prompt = _build_questions_prompt(question_count)
    raw_response = call_llm(system_prompt, job_description, max_tokens=500)
    try:
        result = _extract_json(raw_response)
        return result.get("questions", [])
    except (json.JSONDecodeError, TypeError):
        return []


ANALYSIS_SYSTEM_PROMPT = """You are a recruiting assistant reviewing a candidate's
pre-screening question-and-answer pairs before a human recruiter looks at them.

Flag ONLY real, concrete concerns the candidate explicitly stated in their own
answers — for example: not authorized to work at the company's location without
sponsorship, an explicit availability conflict, unwillingness to relocate or work
on-site when the job requires it, or a salary expectation the candidate themselves
flags as a hard requirement. Do NOT invent or infer concerns that are not clearly
and explicitly stated. A short or plain answer is not a concern by itself.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "has_concerns": boolean,
  "concerns": [string, ...]  // empty array if has_concerns is false
}"""


def analyze_prescreening_answers(qa_pairs: dict) -> dict:
    if not qa_pairs:
        return {"has_concerns": False, "concerns": []}

    user_prompt = "\n".join(f"Q: {q}\nA: {a}" for q, a in qa_pairs.items())
    raw_response = call_llm(ANALYSIS_SYSTEM_PROMPT, user_prompt, max_tokens=400)
    try:
        result = _extract_json(raw_response)
        return {
            "has_concerns": bool(result.get("has_concerns", False)),
            "concerns": result.get("concerns", []) or [],
        }
    except (json.JSONDecodeError, TypeError):
        return {"has_concerns": False, "concerns": []}