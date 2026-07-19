import json

from app.llm_client import call_llm
from app.agents.screening_agent import _extract_json

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

    try:
        return _extract_json(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {
            "justification_quality": None,
            "verdict_reasonable": None,
            "reasoning_notes": "Judge failed to return valid JSON",
        }