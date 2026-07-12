import chromadb

client = chromadb.PersistentClient(path="./.chroma")
collection = client.get_or_create_collection(name="job_postings")


def index_jobs(jobs: list[dict]) -> None:
    
    collection.upsert(
        ids=[job["id"] for job in jobs],
        documents=[job["description"] for job in jobs],
        metadatas=[{"title": job["title"]} for job in jobs],
    )
    print(f"DEBUG indexed {len(jobs)} jobs: {[j['title'] for j in jobs]}")


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

    print("DEBUG retrieved jobs:")
    for m in matches:
        print(f"  - {m['title']} (distance: {m['distance']:.4f})")

    return matches