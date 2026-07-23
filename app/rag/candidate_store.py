import chromadb

client = chromadb.PersistentClient(path="./.chroma")
collection = client.get_or_create_collection(name="candidate_profiles")


def index_candidate(candidate_id: int, name: str, cv_text: str) -> None:
    
    collection.upsert(
        ids=[str(candidate_id)],
        documents=[cv_text],
        metadatas=[{"name": name}],
    )


def search_candidates(query: str, top_k: int = 5) -> list[dict]:
    
    results = collection.query(query_texts=[query], n_results=top_k)

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "candidate_id": int(results["ids"][0][i]),
            "name": results["metadatas"][0][i]["name"],
            "distance": results["distances"][0][i],
        })
    return matches