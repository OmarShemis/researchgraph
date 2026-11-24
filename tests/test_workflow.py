import unittest

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from researchgraph.graphs.rgraph import build_graph


class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_checker_can_read_sources(self):
        calls = []

        @tool
        def mcp_read_webpage(url: str) -> str:
            """Read a fixture source."""
            calls.append(url)
            return "Source supports the claim."

        model = Model(responses=[
            AIMessage(content="Plan"), AIMessage(content="Findings"), AIMessage(content="Analysis"),
            AIMessage(content="", tool_calls=[{
                "name": "mcp_read_webpage", "args": {"url": "https://example.com"}, "id": "read-1",
            }]),
            AIMessage(content="APPROVED\nSource checked."), AIMessage(content="Final report"),
        ])
        result = await build_graph(model, [mcp_read_webpage]).ainvoke(
            {"question": "Test"}, config={"configurable": {"thread_id": "approved"}},
        )
        self.assertEqual(calls, ["https://example.com"])
        self.assertTrue(result["approved"])
        self.assertEqual(result["rounds"], 1)
        self.assertEqual(result["report"], "Final report")

    async def test_retry_then_approval(self):
        result = await self.run_reviews(["RESEARCH_AGAIN\nNeed sources.", "APPROVED"])
        self.assertEqual(result["rounds"], 2)
        self.assertTrue(result["approved"])
        self.assertEqual(result["report"], "Report")

    async def test_two_rejections_stop_with_incomplete_report(self):
        result = await self.run_reviews(["RESEARCH_AGAIN", "RESEARCH_AGAIN\nMissing sources."])
        self.assertEqual(result["rounds"], 2)
        self.assertFalse(result["approved"])
        self.assertTrue(result["report"].startswith("# Incomplete report"))
        self.assertIn("Missing sources.", result["report"])

    async def run_reviews(self, reviews):
        responses = [AIMessage(content="Plan")]
        for review in reviews:
            responses.extend([AIMessage(content="Findings"), AIMessage(content="Analysis"), AIMessage(content=review)])
        responses.append(AIMessage(content="Report"))
        return await build_graph(Model(responses=responses), []).ainvoke(
            {"question": "Test"}, config={"configurable": {"thread_id": "review-test"}},
        )
