''' the orchestrator is "the manager" that calls the screening agent via screen_node → categorize() 
decides the category (suitable / borderline / not suitable / needs review) and saved the result

it touches aldo the matching agent indirectly ( matching agent does RAG retrieval , it finds jobs i chromaDB and then rescore them with the same logic of screening agent )
 !!! No agent everrrr takes an irreversible action by itself ( HR always clicks the final button ) 

 --> SOOO is the whole system orchestrated by LangGraph ??? --> NOOO only screening and matching , other agents are called by app/main.py endpoints 
  WHY ? -->  The Screening Agent (and Matching, which reuses it) is the one place where the AI's output needs to decide what happens next ( 4 different categories as an output )
             and an orchestrator/graph exists to route based on conditions
          The other agents don't produce a result that branches anywhere ( call the LLM once, get a structured answer, show it to HR )  
          
          
          
LangGraph = a collection of nodes and edges that defines the flow of your application logic:
 1. State : A single object (dictionary-like) that holds everything relevant (CV text, job description,the screening result )
 2. Node : A function that takes a State as input and returns a new State as output (e.g. screen_node, categorize, suitable_node, etc.)
 3. Edge : A connection between two nodes, which can be conditional (e.g. if score >= 70 go to suitable_node, else go to borderline_node)
 '''
from typing import TypedDict, Optional
import json as json_lib
from langgraph.graph import StateGraph, END

from app.agents.screening_agent import screen_candidate
from app.db.screenings import save_screening
from app.db.candidates import list_candidates

#state : 
class ScreeningState(TypedDict):
    cv_text: str
    job_description: str
    result: Optional[dict]
    category: Optional[str]

# entry node ( the graph starts here )  --> calls the screening agent and saves the result in state["result"]
# this node does the AI work 
def screen_node(state: ScreeningState) -> ScreeningState:
    result = screen_candidate(state["cv_text"], state["job_description"])
    return {**state, "result": result}

# categorize() is not a node , it just reads the state screen_node just updated 
# decides which of the 4 category nodes to go next (suitable_node, borderline_node, not_suitable_node, needs_review_node)
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


# the 4 category nodes just print the category and return the state with the category added
# they are terminal/end nodes — the graph's exit points, one per possible outcome
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


graph = StateGraph(ScreeningState)  # creates empty graph 
# nodes : 
graph.add_node("screen", screen_node)
graph.add_node("suitable", suitable_node)
graph.add_node("borderline", borderline_node)
graph.add_node("not_suitable", not_suitable_node)
graph.add_node("needs_review", needs_review_node)

graph.set_entry_point("screen")  # Tells the graph: "when someone runs this, start at the node named screen."
# after screen_node runs, the next node is determined by categorize()
graph.add_conditional_edges("screen", categorize, {
    "suitable": "suitable",
    "borderline": "borderline",
    "not_suitable": "not_suitable",
    "needs_review": "needs_review",
})

# whichever of the four category nodes runs, once it's done, the graph is finished.
graph.add_edge("suitable", END)
graph.add_edge("borderline", END)
graph.add_edge("not_suitable", END)
graph.add_edge("needs_review", END)

app = graph.compile()

# public entry point that actually runs the compiled graph
# with a fresh state (cv_text, job_description) and returns the final state (result + category)
def run_screening(cv_text: str, job_description: str) -> dict:
    final_state = app.invoke({
        "cv_text": cv_text,
        "job_description": job_description,
        "result": None,
        "category": None,
    })
    return final_state

# Wraps run_screening, then takes the final result + category and writes it to SQLite via save_screening
def run_and_save_screening(candidate_id: int, job_id: int, cv_text: str, job_description: str) -> dict:
    final_state = run_screening(cv_text, job_description)

    result = final_state["result"]
    result["category"] = final_state["category"]

    save_screening(candidate_id, job_id, result)

    return result


def _build_cv_text_for_screening(candidate: dict) -> str:
    # not a part of the graph 
    # it appends the prescreening Q&A to the CV text stored for one LLM call ( without touchig the database )
    cv_text = candidate["cv_text"]
    if candidate.get("prescreening_answers"):
        try:
            answers = json_lib.loads(candidate["prescreening_answers"])
            qa_block = "\n\nPRE-SCREENING ANSWERS:\n" + "\n".join(f"Q: {q}\nA: {a}" for q, a in answers.items())
            cv_text += qa_block
        except (json_lib.JSONDecodeError, TypeError):
            pass
    return cv_text


def screen_candidates_for_job(candidate_ids: list[int], job_id: int) -> list[dict]:
# takes that whole list of candidate IDs and runs Screening on each one against that same job, then ranks them.
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

        cv_text_for_screening = _build_cv_text_for_screening(candidate)
        result = run_and_save_screening(candidate_id, job_id, cv_text_for_screening, job_description)
        result["candidate_id"] = candidate_id
        result["candidate_name"] = candidate["name"]
        results.append(result)

    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))

    return results  