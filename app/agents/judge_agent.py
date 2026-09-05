import json
import logging

from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """You are an evaluator grading an HR screening assistant's
output. You will be given: a CV, a job description, and the screening assistant's
result (score, verdict, justification). Grade the result against this rubric:

1. justification_quality (1-5): Is the justification specific and grounded in
   the actual CV/job content, or generic and could apply to any candidate?
2. verdict_reasonable (true/false): Given the CV and job, is the verdict
   (Suitable/Borderline/Not suitable) a defensible call a human recruiter
   might also make — even if you might have scored it slightly differently?
3. reasoning_notes (string): 1-2 sentences on any specific issue you noticed,
   or "No issues found" if none.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "justification_quality": number,
  "verdict_reasonable": boolean,
  "reasoning_notes": string
}"""


def _judge_error_result(raw_response) -> dict:
    preview = str(raw_response)[:200] if raw_response else "(empty response)"
    return {
        "justification_quality": None,
        "verdict_reasonable": None,
        "reasoning_notes": f"Judge failed to return valid JSON after retry. Raw: {preview}",
    }


def judge_screening_result(cv_text: str, job_description: str, screening_result: dict) -> dict:

    user_prompt = f"""JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}

SCREENING ASSISTANT'S RESULT:
Score: {screening_result.get('score')}
Verdict: {screening_result.get('verdict')}
Justification: {screening_result.get('justification')}"""

    raw_response = call_llm(JUDGE_SYSTEM_PROMPT, user_prompt, max_tokens=500)
    logger.debug("Judge raw response received (%d chars)", len(raw_response) if raw_response else 0)

    try:
        return _extract_json(raw_response)
    except (json.JSONDecodeError, TypeError):
        if not raw_response:
            retry_response = call_llm(JUDGE_SYSTEM_PROMPT, user_prompt, max_tokens=500)
        else:
            fix_prompt = f"""Your previous response was not a clean JSON object. Here it is:
{raw_response}

Return ONLY the corrected, valid JSON object in the exact shape requested. No markdown
fences, no reasoning, no text before or after it. Start with {{ and end with }}."""
            retry_response = call_llm(JUDGE_SYSTEM_PROMPT, fix_prompt, max_tokens=500)

        logger.debug("Judge retry response received (%d chars)", len(retry_response) if retry_response else 0)

        try:
            return _extract_json(retry_response)
        except (json.JSONDecodeError, TypeError):
            return _judge_error_result(retry_response)