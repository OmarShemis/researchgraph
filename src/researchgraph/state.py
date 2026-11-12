"""Shared state for one research request."""

import operator
from typing import Annotated, TypedDict


class Finding(TypedDict):
    task: str
    snippet: str


class ResearchState(TypedDict, total=False):
    question: str
    research_tasks: list[str]
    findings: Annotated[list[Finding], operator.add]
    critique: str
    needs_more_research: bool
    research_rounds: int
    final_report: str
