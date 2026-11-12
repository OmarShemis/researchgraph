"""Bounded planner -> researcher -> reviewer -> writer workflow."""

from langgraph.graph import START, END, StateGraph
from .nodes import build_nodes, route_after_review
from .state import ResearchState


def build_graph(agents, max_rounds=2):
    if not 1 <= max_rounds <= 5:
        raise ValueError("max_rounds must be between 1 and 5.")
    graph = StateGraph(ResearchState)
    for name, node in build_nodes(agents).items():
        graph.add_node(name, node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        lambda state: route_after_review(state, max_rounds),
        {"researcher": "researcher", "writer": "writer"},
    )
    graph.add_edge("writer", END)
    return graph.compile()
