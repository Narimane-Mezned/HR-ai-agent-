
from app.rag.job_store import find_matching_jobs
from app.agents.screening_agent import screen_candidate


def match_candidate_to_jobs(cv_text: str, top_k: int = 3) -> list[dict]:
   
    retrieved_jobs = find_matching_jobs(cv_text, top_k=top_k)

    results = []
    for job in retrieved_jobs:
        screening_result = screen_candidate(cv_text, job["description"])
        screening_result["job_id"] = job["id"]
        screening_result["job_title"] = job["title"]
        screening_result["retrieval_distance"] = job["distance"]
        results.append(screening_result)

    
    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))

    return results