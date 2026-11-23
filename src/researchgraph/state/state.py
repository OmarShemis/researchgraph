from typing import TypedDict


class ResearchState(TypedDict, total=False):
    question: str
    plan: str
    findings: str
    analysis: str
    review: str
    rounds: int
    report: str
