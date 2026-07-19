
import json
import re
from app.db.cache import make_cache_key, get_cached_result, save_cached_result
from app.config import OPENROUTER_MODEL_CHEAP
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
- Base the score only on what's in the CV and job description below.
- Do NOT think out loud, show your reasoning process, or write any explanation
  outside the JSON object. Any internal reasoning must stay inside the
  "years_experience_reasoning" and "justification" fields, briefly. Your entire
  response must be a single JSON object, starting with { and ending with }. No
  markdown code fences, no commentary before or after."""

def _extract_json(raw_text: str) -> dict:
    if raw_text is None:
        raise json.JSONDecodeError("Response was None", "", 0)

    text = raw_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        return json.loads(candidate)  

    raise json.JSONDecodeError("No JSON object found in response", text, 0)


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


def screen_candidate(cv_text: str, job_description: str, model: str = OPENROUTER_MODEL_CHEAP) -> dict:
    clean_cv_text = redact_pii(cv_text)

    cache_key = make_cache_key(clean_cv_text, job_description, model)
    cached = get_cached_result(cache_key)
    if cached:
        print("DEBUG: cache HIT — skipping LLM call")
        return cached

    user_prompt = f"JOB DESCRIPTION:\n{job_description}\n\nCANDIDATE CV:\n{clean_cv_text}"

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, model=model, max_tokens=2500)
    print("DEBUG raw_response:", repr(raw_response))

    try:
        result = _extract_json(raw_response)
    except (json.JSONDecodeError, TypeError):
        if not raw_response:
            retry_response = call_llm(SYSTEM_PROMPT, user_prompt, max_tokens=1500)
        else:
            fix_prompt = f"""Your previous response was not a clean JSON object. Here it is:
{raw_response}

Return ONLY the corrected, valid JSON object in the exact shape requested. No markdown
fences, no reasoning, no text before or after it. Start with {{ and end with }}."""
            retry_response = call_llm(SYSTEM_PROMPT, fix_prompt, max_tokens=1500)

        print("DEBUG retry_response:", repr(retry_response))

        try:
            result = _extract_json(retry_response)
        except (json.JSONDecodeError, TypeError):
            return _error_result(retry_response)

    if "skills" in result and isinstance(result["skills"], list):
        result["skills"] = _filter_hallucinated_skills(result["skills"], clean_cv_text)

    save_cached_result(cache_key, result, model)
    return result