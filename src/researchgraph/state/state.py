from typing import TypedDict


class ResearchState(TypedDict, total=False):
    question: str
    plan: str
    findings: list[dict]
    research_gaps: list[str]
    verified_findings: list[dict]
    gaps: list[str]
    approved: bool
    analysis: str
    review: str
    rounds: int
    report: str
