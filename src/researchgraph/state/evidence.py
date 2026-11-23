import json
from typing import Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    claim: str = Field(min_length=1)
    source_url: str = Field(description="HTTP(S) URL of a page successfully read with the webpage tool")
    supporting_text: str = Field(min_length=1, description="Exact passage from that page supporting this claim")


class ResearchFindings(BaseModel):
    findings: list[Finding]
    gaps: list[str] = Field(description="Requested topics or evidence still missing")


class ClaimCheck(BaseModel):
    claim_id: str
    verdict: Literal["supported", "contradicted", "unverified"]
    source_url: str
    supporting_text: str
    correction: str = Field(description="Specific correction or research action; empty if supported")


class VerificationReport(BaseModel):
    checks: list[ClaimCheck]
    gaps: list[str] = Field(description="Missing coverage or counterevidence that prevents approval")


def _page(content):
    """Extract a successful webpage payload from MCP text blocks."""
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (ValueError, TypeError):
            return None
    if isinstance(content, list):
        for block in content:
            page = _page(block.get("text", "")) if isinstance(block, dict) else _page(block)
            if page:
                return page
    if isinstance(content, dict) and not content.get("error"):
        if content.get("text") and content.get("url"):
            return content
    return None


def read_sources(messages):
    """Only tool results from actual webpage reads count; search snippets do not."""
    calls, sources = {}, {}
    for message in messages:
        for call in getattr(message, "tool_calls", []):
            calls[call["id"]] = call
        if message.type != "tool" or getattr(message, "status", "success") == "error":
            continue
        call = calls.get(message.tool_call_id, {})
        if call.get("name") != "mcp_read_webpage":
            continue
        page = _page(message.content)
        if page:
            sources[page["url"]] = page["text"]
            sources[call["args"]["url"]] = page["text"]
    return sources


def has_passage(url, passage, sources):
    normalize = lambda text: " ".join(text.split())
    return (
        url.startswith(("http://", "https://")) and bool(passage.strip())
        and url in sources and normalize(passage) in normalize(sources[url])
    )
