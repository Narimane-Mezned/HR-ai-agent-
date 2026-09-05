import logging
import chromadb

logger = logging.getLogger(__name__)

client = chromadb.PersistentClient(path="./.chroma")
collection = client.get_or_create_collection(name="job_postings")


def index_jobs(jobs: list[dict]) -> None:
    collection.upsert(
        ids=[job["id"] for job in jobs],
        documents=[job["description"] for job in jobs],
        metadatas=[
            {
                "title": job["title"],
                "created_by": job.get("created_by") or "",
                "location": job.get("location") or "",
                "remote_policy": job.get("remote_policy") or "",
                "experience_level": job.get("experience_level") or "",
            }
            for job in jobs
        ],
    )
    logger.debug("Indexed %d jobs: %s", len(jobs), [j['title'] for j in jobs])


def _build_where(filters: dict) -> dict | None:
    clauses = [{field: {"$eq": value}} for field, value in filters.items() if value]
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def find_matching_jobs(
    candidate_profile_text: str,
    top_k: int = 3,
    created_by: str = None,
    location: str = None,
    remote_policy: str = None,
    experience_level: str = None,
) -> list[dict]:
    where = _build_where({
        "created_by": created_by,
        "location": location,
        "remote_policy": remote_policy,
        "experience_level": experience_level,
    })

    results = collection.query(
        query_texts=[candidate_profile_text],
        n_results=top_k,
        where=where,
    )

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "description": results["documents"][0][i],
            "distance": results["distances"][0][i],
        })

    logger.debug("Retrieved %d matching jobs (where=%s)", len(matches), where)
    for m in matches:
        logger.debug("  - %s (distance: %.4f)", m['title'], m['distance'])

    return matches