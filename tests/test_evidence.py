import json
import unittest

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from researchgraph.agents.fact_checker import create_fact_checker
from researchgraph.agents.report_writer import write_report
from researchgraph.graphs.rgraph import build_graph
from researchgraph.state.evidence import has_passage, read_sources

URL = "https://example.com/docs"
PASSAGE = "The framework supports conditional routing."
FINDING = {"claim": "Conditional routing is supported", "source_url": URL, "supporting_text": PASSAGE}


def output(name, args, identifier="output"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": identifier}])


class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class EvidenceTests(unittest.IsolatedAsyncioTestCase):
    def test_only_successful_page_reads_count(self):
        messages = [
            output("mcp_web_search", {"query": "routing"}, "search"),
            ToolMessage(content=json.dumps({"url": URL, "text": PASSAGE}), tool_call_id="search"),
            output("mcp_read_webpage", {"url": URL}, "blocked"),
            ToolMessage(content=json.dumps({"url": URL, "error": "403 Forbidden"}), tool_call_id="blocked"),
        ]
        self.assertEqual(read_sources(messages), {})
        messages.extend([
            output("mcp_read_webpage", {"url": URL}, "read"),
            ToolMessage(content=[{"type": "text", "text": json.dumps({"url": URL, "text": PASSAGE})}], tool_call_id="read"),
        ])
        sources = read_sources(messages)
        self.assertTrue(has_passage(URL, PASSAGE, sources))
        self.assertFalse(has_passage(URL, "An invented quotation.", sources))
        self.assertFalse(has_passage("https://fake.example", PASSAGE, sources))

    async def test_research_and_checker_both_read_sources(self):
        reads = []

        @tool
        def mcp_read_webpage(url: str) -> str:
            """Read a fixture source."""
            reads.append(url)
            return json.dumps({"url": url, "text": PASSAGE})

        check = {"claim_id": "C1", "verdict": "supported", "source_url": URL,
                 "supporting_text": PASSAGE, "correction": ""}
        model = Model(responses=[
            AIMessage(content="Read official documentation."),
            output("mcp_read_webpage", {"url": URL}, "research-read"),
            output("ResearchFindings", {"findings": [FINDING], "gaps": []}, "findings"),
            AIMessage(content="Analysis based on C1."),
            output("mcp_read_webpage", {"url": URL}, "verification-read"),
            output("VerificationReport", {"checks": [check], "gaps": []}, "checks"),
            AIMessage(content=f"Routing is supported. [Documentation]({URL})"),
        ])
        result = await build_graph(model, [mcp_read_webpage]).ainvoke(
            {"question": "Does it support routing?"},
            config={"configurable": {"thread_id": "verified"}},
        )
        self.assertEqual(reads, [URL, URL])
        self.assertTrue(result["approved"])
        self.assertEqual(len(result["verified_findings"]), 1)
        self.assertFalse(result["report"].startswith("# Incomplete report"))

    async def test_checker_cannot_approve_without_its_own_read(self):
        check = {"claim_id": "C1", "verdict": "supported", "source_url": URL,
                 "supporting_text": PASSAGE, "correction": ""}
        model = Model(responses=[output("VerificationReport", {"checks": [check], "gaps": []})])
        result = await create_fact_checker(model, [])({
            "question": "Test", "plan": "Plan", "analysis": "Analysis",
            "findings": [{**FINDING, "claim_id": "C1"}], "research_gaps": [],
        })
        self.assertFalse(result["approved"])
        self.assertEqual(result["verified_findings"], [])
        self.assertIn("C1", result["review"])

    async def test_unread_evidence_retries_then_marks_incomplete(self):
        responses = [AIMessage(content="Plan")]
        for number in (1, 2):
            responses.extend([
                output("ResearchFindings", {"findings": [FINDING], "gaps": []}, f"findings-{number}"),
                AIMessage(content="Insufficient evidence."),
                output("VerificationReport", {"checks": [], "gaps": []}, f"review-{number}"),
            ])
        result = await build_graph(Model(responses=responses), []).ainvoke(
            {"question": "Test"}, config={"configurable": {"thread_id": "incomplete"}},
        )
        self.assertEqual(result["rounds"], 2)
        self.assertFalse(result["approved"])
        self.assertTrue(result["report"].startswith("# Incomplete report"))
        self.assertIn("No evidence passed", result["report"])

    async def test_writer_withholds_invented_citations(self):
        result = await write_report({
            "question": "Test", "verified_findings": [FINDING], "gaps": [], "approved": True,
        }, Model(responses=[AIMessage(content="Claim. [Fake](https://fake.example)")]))
        self.assertTrue(result["report"].startswith("# Incomplete report"))
        self.assertNotIn("https://fake.example", result["report"])
        self.assertIn(URL, result["report"])
