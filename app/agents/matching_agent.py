from app.rag.job_store import find_matching_jobs
from app.agents.screening_agent import screen_candidate


def match_candidate_to_jobs(
    cv_text: str,
    created_by: str,
    top_k: int = 3,
    location: str = None,
    remote_policy: str = None,
    experience_level: str = None,
) -> list[dict]:

    retrieved_jobs = find_matching_jobs(
        cv_text,
        top_k=top_k,
        created_by=created_by,
        location=location,
        remote_policy=remote_policy,
        experience_level=experience_level,
    )

    results = []
    for job in retrieved_jobs:
        screening_result = screen_candidate(cv_text, job["description"])
        screening_result["job_id"] = job["id"]
        screening_result["job_title"] = job["title"]
        screening_result["retrieval_distance"] = job["distance"]
        results.append(screening_result)

    
    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))

    return results