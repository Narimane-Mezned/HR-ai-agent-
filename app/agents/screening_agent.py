import json
import re
import logging
from app.db.cache import make_cache_key, get_cached_result, save_cached_result
from app.config import OPENROUTER_MODEL_CHEAP, OPENROUTER_MODEL_STRONG
from app.llm_client import call_llm
from app.pdf_utils import redact_pii

logger = logging.getLogger(__name__)

ROUTING_MARGIN = 8


# this is the prompt engineering 
# the fixed rulebook sent on every LLM call 
SYSTEM_PROMPT = """You are an HR screening assistant. Given a candidate's CV text
and a job description, evaluate how well the candidate fits the job.

Return ONLY a JSON object with this exact shape, no text before or after it:
{
  "name": string,
  "years_experience": number,
  "years_experience_reasoning": string,  // briefly explain how you calculated this
  "skills": [string],       // ONLY skills that are literally written in the CV text
  "education": string,      // highest degree/qualification literally stated in the CV, or "" if none stated
  "languages": [string],    // languages literally mentioned in the CV (spoken or written)
  "location": string,       // candidate's city/region literally stated in the CV, or "" if none stated
  "confidence_level": string,      // one of: "high", "medium", "low"
  "confidence_reasoning": string,  // 1 sentence: why this confidence level
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
- For "education" and "location", only report what is literally written in the CV.
  Leave as "" rather than guessing or inferring.
- For "confidence_level", use "low" whenever the CV is primarily project-based
  without traditional job history, has ambiguous or missing dates, or is otherwise
  hard to evaluate confidently. Use "high" only when the CV clearly states relevant,
  dated experience directly comparable to the job description.
- Base the score only on what's in the CV and job description below.
- Do NOT think out loud, show your reasoning process, or write any explanation
  outside the JSON object. Any internal reasoning must stay inside the
  "years_experience_reasoning", "confidence_reasoning" and "justification" fields,
  briefly. Your entire response must be a single JSON object, starting with { and
  ending with }. No markdown code fences, no commentary before or after."""

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

# the guardrail
def _filter_hallucinated_skills(skills: list, cv_text: str) -> list:
    # lowercase the CV, lowercase each claimed skill, keep only skills that literally appear as a substring.
    # No AI judgment here at all
    cv_lower = cv_text.lower()
    return [skill for skill in skills if skill.lower() in cv_lower]

# If even the retry fails to parse, don't crash 
# return a structured object with verdict: "Error"
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

def _is_ambiguous_score(score) -> bool:
    if score is None:
        return False
    return (
        abs(score - 70) <= ROUTING_MARGIN
        or abs(score - 40) <= ROUTING_MARGIN
    )


def _run_screening_call(clean_cv_text: str, job_description: str, model: str) -> dict:
    user_prompt = f"JOB DESCRIPTION:\n{job_description}\n\nCANDIDATE CV:\n{clean_cv_text}"

    raw_response = call_llm(SYSTEM_PROMPT, user_prompt, model=model, max_tokens=2500)
    logger.debug("LLM raw response received (%d chars)", len(raw_response) if raw_response else 0)

    try:
        return _extract_json(raw_response)
    except (json.JSONDecodeError, TypeError):
        if not raw_response:
            retry_response = call_llm(SYSTEM_PROMPT, user_prompt, model=model, max_tokens=1500)
        else:
            fix_prompt = f"""Your previous response was not a clean JSON object. Here it is:
{raw_response}

Return ONLY the corrected, valid JSON object in the exact shape requested. No markdown
fences, no reasoning, no text before or after it. Start with {{ and end with }}."""
            retry_response = call_llm(SYSTEM_PROMPT, fix_prompt, model=model, max_tokens=1500)

        logger.debug("LLM retry response received (%d chars)", len(retry_response) if retry_response else 0)

        try:
            return _extract_json(retry_response)
        except (json.JSONDecodeError, TypeError):
            return _error_result(retry_response)


# the orchestration inside the agent
def screen_candidate(
    cv_text: str,
    job_description: str,
    model: str = OPENROUTER_MODEL_CHEAP,
    bypass_cache: bool = False,
) -> dict:
    clean_cv_text = redact_pii(cv_text)  # "Redact PII" means strip out personally identifiable information before the text leaves your system

    cache_key = make_cache_key(clean_cv_text, job_description, model)
    if not bypass_cache:
        cached = get_cached_result(cache_key)
        if cached:
            logger.debug("Cache hit for screening request — skipping LLM call")
            return cached

    result = _run_screening_call(clean_cv_text, job_description, model)

    if "skills" in result and isinstance(result["skills"], list):
        result["skills"] = _filter_hallucinated_skills(result["skills"], clean_cv_text)

    if "score" in result:
        result["verdict"] = _normalize_verdict(result["score"])

    result["routed_to_strong_model"] = False

    if model == OPENROUTER_MODEL_CHEAP and _is_ambiguous_score(result.get("score")):
        strong_result = _run_screening_call(clean_cv_text, job_description, OPENROUTER_MODEL_STRONG)
        if strong_result.get("verdict") != "Error" and strong_result.get("score") is not None:
            if "skills" in strong_result and isinstance(strong_result["skills"], list):
                strong_result["skills"] = _filter_hallucinated_skills(strong_result["skills"], clean_cv_text)
            strong_result["verdict"] = _normalize_verdict(strong_result["score"])
            strong_result["routed_to_strong_model"] = True
            result = strong_result

    if not bypass_cache and result.get("verdict") != "Error":
        save_cached_result(cache_key, result, model)

    return result

# the other guardrail
# normalizes the score into a verdict string using fixed thresholds 
def _normalize_verdict(score) -> str:
    if score is None:
        return "Error"
    elif score >= 70:
        return "Suitable"
    elif score >= 40:
        return "Borderline"
    else:
        return "Not suitable"