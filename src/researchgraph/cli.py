"""Interactive research CLI with persistent MCP lifetime."""

import asyncio
import sys
from langchain.mcp import MCPAdapter
from .agents import build_agents
from .config import Settings
from .graph import build_graph
from .notes_db import database_path


async def chat(settings):
    config = {
        "mcpServers": {
            "notes": {
                "command": sys.executable,
                "args": ["-m", "researchgraph.notes_mcp"],
                "env": {"RESEARCHGRAPH_NOTES_DB": str(database_path().resolve())},
            }
        }
    }
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        app = build_graph(build_agents(settings, tools), settings.max_research_rounds)
        print("ResearchGraph ready. Type 'quit' to exit.")
        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if question.lower() in {"quit", "exit"}:
                break
            if not question:
                continue
            try:
                result = await app.ainvoke(
                    {"question": question, "findings": []}, {"recursion_limit": 32}
                )
                print(f"\n{result['final_report']}\n")
            except Exception as error:
                print(
                    f"Research failed ({type(error).__name__}). Check Ollama, Tavily and the model's tool support."
                )


def main():
    try:
        settings = Settings.from_environment()
        asyncio.run(chat(settings))
    except KeyboardInterrupt:
        pass
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(
            f"Startup failed ({type(error).__name__}). Check dependencies and local MCP configuration.",
            file=sys.stderr,
        )
        return 1
    return 0
