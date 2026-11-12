import os
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch

from researchgraph.graph import build_graph
from researchgraph.nodes import response_text
from researchgraph.notes_db import add_note, delete_note, list_notes


class FakeAgent:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.prompts = []

    async def ainvoke(self, request, config=None):
        self.prompts.append(request["messages"][0]["content"])
        return {"messages": [{"content": next(self.responses)}]}


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    def agents(self, reviews):
        return {
            "planner": FakeAgent(["Find costs\nFind benefits\nFind risks"]),
            "researcher": FakeAgent(
                [f"Evidence {i}: https://example.org/{i}" for i in range(20)]
            ),
            "reviewer": FakeAgent(reviews),
            "writer": FakeAgent(["Final report"]),
        }

    async def test_ready_goes_directly_to_writer(self):
        agents = self.agents(["READY\nEnough evidence."])
        result = await build_graph(agents).ainvoke(
            {"question": "Compare options", "findings": []}
        )
        self.assertEqual(result["final_report"], "Final report")
        self.assertEqual(result["research_rounds"], 1)
        self.assertEqual(len(result["findings"]), 3)

    async def test_review_loop_is_bounded_and_critique_reaches_researcher(self):
        agents = self.agents(["MORE_RESEARCH\nFind missing costs."] * 2)
        result = await build_graph(agents, max_rounds=2).ainvoke(
            {"question": "Compare", "findings": []}
        )
        self.assertEqual(result["research_rounds"], 2)
        self.assertEqual(len(result["findings"]), 6)
        self.assertEqual(len(result["research_tasks"]), 3)
        self.assertIn("Find missing costs", agents["researcher"].prompts[3])
        self.assertIn("MORE_RESEARCH", agents["writer"].prompts[0])

    async def test_blank_question_rejected(self):
        with self.assertRaises(ValueError):
            await build_graph(self.agents([])).ainvoke({"question": " "})

    def test_text_content_blocks(self):
        self.assertEqual(
            response_text(
                {"messages": [{"content": [{"type": "text", "text": "hello"}]}]}
            ),
            "hello",
        )

    async def test_real_stdio_mcp_notes_lifecycle(self):
        from langchain.mcp import MCPAdapter

        with TemporaryDirectory() as folder:
            path = str(Path(folder) / "notes.db")
            config = {
                "mcpServers": {
                    "notes": {
                        "command": sys.executable,
                        "args": ["-m", "researchgraph.notes_mcp"],
                        "env": {"RESEARCHGRAPH_NOTES_DB": path},
                    }
                }
            }
            async with MCPAdapter(config) as adapter:
                tools = await adapter.list_tools()
                add = next(tool for tool in tools if tool.name.endswith("add_a_note"))
                listing = next(
                    tool for tool in tools if tool.name.endswith("list_my_notes")
                )
                delete = next(
                    tool for tool in tools if tool.name.endswith("delete_a_note")
                )
                await add.ainvoke({"text": "offline MCP test note"})
                self.assertIn("offline MCP test note", str(await listing.ainvoke({})))
                await delete.ainvoke({"note_id": 1})
                with patch.dict(os.environ, {"RESEARCHGRAPH_NOTES_DB": path}):
                    self.assertEqual(list_notes("local"), [])


class StorageTests(unittest.TestCase):
    def test_owner_isolation_and_validation(self):
        with (
            TemporaryDirectory() as folder,
            patch.dict(
                os.environ, {"RESEARCHGRAPH_NOTES_DB": str(Path(folder) / "notes.db")}
            ),
        ):
            note = add_note("alice", "private note")
            self.assertEqual(list_notes("bob"), [])
            self.assertFalse(delete_note("bob", note["id"]))
            self.assertEqual(len(list_notes("alice")), 1)
            self.assertTrue(delete_note("alice", note["id"]))
            with self.assertRaises(ValueError):
                add_note("alice", " ")

    def test_configuration_validation(self):
        from researchgraph.config import Settings

        with (
            patch("researchgraph.config.load_dotenv"),
            patch.dict(os.environ, {"TAVILY_API_KEY": "", "MAX_RESEARCH_ROUNDS": "2"}),
        ):
            with self.assertRaisesRegex(ValueError, "TAVILY_API_KEY"):
                Settings.from_environment()
        with (
            patch("researchgraph.config.load_dotenv"),
            patch.dict(
                os.environ, {"TAVILY_API_KEY": "test-only", "MAX_RESEARCH_ROUNDS": "0"}
            ),
        ):
            with self.assertRaisesRegex(ValueError, "MAX_RESEARCH_ROUNDS"):
                Settings.from_environment()


if __name__ == "__main__":
    unittest.main()
