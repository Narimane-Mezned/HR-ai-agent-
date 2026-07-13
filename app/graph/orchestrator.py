from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.agents.screening_agent import screen_candidate
from app.db.screenings import save_screening
from app.db.candidates import list_candidates

class ScreeningState(TypedDict):
    cv_text: str
    job_description: str
    result: Optional[dict]
    category: Optional[str]  


def screen_node(state: ScreeningState) -> ScreeningState:
    
    result = screen_candidate(state["cv_text"], state["job_description"])
    return {**state, "result": result}


def categorize(state: ScreeningState) -> str:
    
    result = state["result"]

    if result.get("verdict") == "Error":
        return "needs_review"  

    score = result.get("score")
    if score is None:
        return "needs_review"
    elif score >= 70:
        return "suitable"
    elif score >= 40:
        return "borderline"
    else:
        return "not_suitable"


def suitable_node(state: ScreeningState) -> ScreeningState:
    print(f"Category: SUITABLE (score: {state['result'].get('score')})")
    return {**state, "category": "suitable"}


def borderline_node(state: ScreeningState) -> ScreeningState:
    print(f"Category: BORDERLINE (score: {state['result'].get('score')})")
    return {**state, "category": "borderline"}


def not_suitable_node(state: ScreeningState) -> ScreeningState:
    print(f"Category: NOT SUITABLE (score: {state['result'].get('score')})")
    return {**state, "category": "not_suitable"}


def needs_review_node(state: ScreeningState) -> ScreeningState:
    print("Category: NEEDS REVIEW (screening failed or returned no score)")
    return {**state, "category": "needs_review"}


graph = StateGraph(ScreeningState)
graph.add_node("screen", screen_node)
graph.add_node("suitable", suitable_node)
graph.add_node("borderline", borderline_node)
graph.add_node("not_suitable", not_suitable_node)
graph.add_node("needs_review", needs_review_node)

graph.set_entry_point("screen")
graph.add_conditional_edges("screen", categorize, {
    "suitable": "suitable",
    "borderline": "borderline",
    "not_suitable": "not_suitable",
    "needs_review": "needs_review",
})
graph.add_edge("suitable", END)
graph.add_edge("borderline", END)
graph.add_edge("not_suitable", END)
graph.add_edge("needs_review", END)

app = graph.compile()


def run_screening(cv_text: str, job_description: str) -> dict:
   
    final_state = app.invoke({
        "cv_text": cv_text,
        "job_description": job_description,
        "result": None,
        "category": None,
    })
    return final_state




def run_and_save_screening(candidate_id: int, job_id: int, cv_text: str, job_description: str) -> dict:
   
    final_state = run_screening(cv_text, job_description)

    result = final_state["result"]
    result["category"] = final_state["category"] 

    save_screening(candidate_id, job_id, result)

    return result


def screen_candidates_for_job(candidate_ids: list[int], job_id: int) -> list[dict]:
    
    from app.db.jobs import get_job
    from app.db.candidates import get_candidate

    job = get_job(job_id)
    if not job:
        raise ValueError(f"No job found with id {job_id}")

    job_description = job["description"]
    results = []

    for candidate_id in candidate_ids:
        candidate = get_candidate(candidate_id)
        if not candidate:
            print(f"WARNING: no candidate found with id {candidate_id}, skipping")
            continue

        result = run_and_save_screening(candidate_id, job_id, candidate["cv_text"], job_description)
        result["candidate_id"] = candidate_id
        result["candidate_name"] = candidate["name"]
        results.append(result)

    
    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))

    return results