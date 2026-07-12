import json

from app.llm_client import call_llm
from app.pdf_utils import redact_pii

SYSTEM_PROMPT = """You are an HR screening assistant. Given a candidate's CV text
and a job description, evaluate how well the candidate fits the job.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "name": string,
  "years_experience": number,
  "years_experience_reasoning": string,  // briefly explain how you calculated this
  "skills": [string],       // ONLY skills that are literally written in the CV text
  "score": number,          // 0-100, how well the candidate matches the job
  "verdict": string,        // one of: "Suitable", "Borderline", "Not suitable"
  "justification": string   // 1-2 sentences explaining the score
}

CRITICAL RULES:
- Only include a skill in "skills" if that exact word or a close variant appears
  literally in the CV text. Do NOT infer skills from context (e.g. do not add
  "Kubernetes" just because the candidate mentions "microservices" or "backend").
- For "years_experience", only count explicit dated roles/experience mentioned
  in the CV. If the candidate is a student with mostly projects and no traditional
  job history, say so in years_experience_reasoning and give a conservative estimate.
- Base the score only on what's in the CV and job description below."""


def _filter_hallucinated_skills(skills: list, cv_text: str) -> list:
    
    cv_lower = cv_text.lower()
    return [skill for skill in skills if skill.lower() in cv_lower]


def _error_result(raw_response) -> dict:
    preview = str(raw_response)[:200] if raw_response else "(empty response)"
    return {
        "name": "PARSE_ERROR",
        "years_experience": None,
        "skills": [],
        "score": None,
        "verdict": "Error",
        "justification": f"LLM failed to return valid JSON after retry. Raw: {preview}",
    }


def screen_candidate(cv_text: str, job_description: str) -> dict:
    
    clean_cv_text = redact_pii(cv_text)
    user_prompt = f"JOB DESCRIPTION:\n{job_description}\n\nCANDIDATE CV:\n{clean_cv_text}"

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=1500)
    print("DEBUG raw_response:", repr(raw_response))

    try:
        result = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        if not raw_response:
            # empty response — just retry the original question, nothing to "fix"
            retry_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=1500)
        else:
            # got text back, but it wasn't valid JSON — ask the model to fix it
            fix_prompt = f"""Your previous response was not valid JSON. Here it is:
{raw_response}

Return ONLY the corrected, valid JSON object in the exact shape requested. No other text."""
            retry_response = call_llm(SYSTEM_PROMPT, fix_prompt, max_tokens=1500)

        print("DEBUG retry_response:", repr(retry_response))

        try:
            result = json.loads(retry_response)
        except (json.JSONDecodeError, TypeError):
            return _error_result(retry_response)

    
    if "skills" in result and isinstance(result["skills"], list):
        result["skills"] = _filter_hallucinated_skills(result["skills"], clean_cv_text)

    return result