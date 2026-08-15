import logging
import chromadb

logger = logging.getLogger(__name__)

client = chromadb.PersistentClient(path="./.chroma")
collection = client.get_or_create_collection(name="job_postings")


def index_jobs(jobs: list[dict]) -> None:
    collection.upsert(
        ids=[job["id"] for job in jobs],
        documents=[job["description"] for job in jobs],
        metadatas=[{"title": job["title"]} for job in jobs],
    )
    logger.debug("Indexed %d jobs: %s", len(jobs), [j['title'] for j in jobs])


def find_matching_jobs(candidate_profile_text: str, top_k: int = 3) -> list[dict]:
    results = collection.query(
        query_texts=[candidate_profile_text],
        n_results=top_k,
    )

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "description": results["documents"][0][i],
            "distance": results["distances"][0][i],
        })

    logger.debug("Retrieved %d matching jobs", len(matches))
    for m in matches:
        logger.debug("  - %s (distance: %.4f)", m['title'], m['distance'])

    return matches