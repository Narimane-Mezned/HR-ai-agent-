
from typing import TypedDict
from langgraph.graph import StateGraph, END


class GraphState(TypedDict):
    score: int
    verdict: str


def screen(state: GraphState) -> GraphState:
    print(f"Screening... score is {state['score']}")
    return state


def shortlist(state: GraphState) -> GraphState:
    print("Routed to: SHORTLIST")
    return {**state, "verdict": "shortlisted"}


def reject(state: GraphState) -> GraphState:
    print("Routed to: REJECT")
    return {**state, "verdict": "rejected"}


def route_by_score(state: GraphState) -> str:
    """This function decides WHICH node to go to next, based on state."""
    if state["score"] >= 50:
        return "shortlist"
    else:
        return "reject"


graph = StateGraph(GraphState)
graph.add_node("screen", screen)
graph.add_node("shortlist", shortlist)
graph.add_node("reject", reject)

graph.set_entry_point("screen")
graph.add_conditional_edges("screen", route_by_score, {
    "shortlist": "shortlist",
    "reject": "reject",
})
graph.add_edge("shortlist", END)
graph.add_edge("reject", END)

app = graph.compile()

if __name__ == "__main__":
    print("--- Testing high score ---")
    result_high = app.invoke({"score": 85, "verdict": ""})
    print("Final:", result_high)

    print("\n--- Testing low score ---")
    result_low = app.invoke({"score": 20, "verdict": ""})
    print("Final:", result_low)