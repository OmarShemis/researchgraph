from functools import partial

from langgraph.graph import END, START, StateGraph

from researchgraph.agents.analyst import analyze
from researchgraph.agents.fact_checker import create_fact_checker
from researchgraph.agents.report_writer import write_report
from researchgraph.agents.researcher import create_researcher
from researchgraph.agents.supervisor import supervise
from researchgraph.memory.store import create_memory
from researchgraph.state.state import ResearchState


def after_review(state):
    approved = state["review"].strip().splitlines()[:1] == ["APPROVED"]
    return "report_writer" if approved or state["rounds"] >= 2 else "researcher"


def build_graph(model, tools):
    graph = StateGraph(ResearchState)
    graph.add_node("supervisor", partial(supervise, model=model))
    graph.add_node("researcher", create_researcher(model, tools))
    graph.add_node("analyst", partial(analyze, model=model))
    graph.add_node("fact_checker", create_fact_checker(model, tools))
    graph.add_node("report_writer", partial(write_report, model=model))

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "fact_checker")
    graph.add_conditional_edges("fact_checker", after_review, {
        "researcher": "researcher",
        "report_writer": "report_writer",
    })
    graph.add_edge("report_writer", END)
    return graph.compile(checkpointer=create_memory())
