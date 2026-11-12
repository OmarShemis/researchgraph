# ResearchGraph

A command-line multi-agent research workflow built with LangGraph and LangChain. A local Ollama model plans research, searches through Tavily, reviews the findings, and writes a report. A local stdio MCP server exposes SQLite notes tools to the researcher.

## Workflow

Planner -> Researcher -> Reviewer -> Writer. The reviewer may request another research pass, capped by `MAX_RESEARCH_ROUNDS` (default 2, maximum 5). Each follow-up receives the previous critique; accumulated findings reach the writer. Each question starts fresh workflow state.

## Setup

Requires Python 3.11+, uv, Ollama with a tool-capable model, and a Tavily API key.

```powershell
uv sync
Copy-Item .env.example .env
# Edit .env and set TAVILY_API_KEY.
ollama pull qwen3.5:4b
uv run researchgraph
```

With pip: `python -m pip install -r requirements.txt`, then `researchgraph`. You can also use `python -m researchgraph` after installation. The old `python src/main.py` entry point remains available.

The `.env` in the current working directory is loaded first. The old `src/.env` is supported locally as a fallback, without overriding existing settings. Neither file is committed. The default model endpoint is `http://localhost:11434/v1`.

## Notes MCP server

The CLI launches its own server with the active Python interpreter, so it does not depend on a relative script path. Run it separately with `uv run researchgraph-notes` when connecting another MCP client. Tools list, add and delete local notes. This is a local stdio server, not a multi-user authenticated web service.

Default database: `./data/notes.db`. Override using `RESEARCHGRAPH_NOTES_DB`; point it at an older database to keep using existing notes. No notes are migrated automatically. Model access to deletion is not a security boundary: use this learning project with disposable or backed-up notes.

## Development

```powershell
uv run python -m unittest discover -s tests -v
uv build
```

`src/researchgraph/`: `agents.py` builds the roles; `nodes.py` implements the async steps; `graph.py` defines bounded routing; `config.py` reads startup settings; `notes_db.py` stores notes; `notes_mcp.py` serves tools; `cli.py` manages the session.

Uses LangChain's first-party `MCPAdapter` with FastMCP 4. The previous separate MCP adapter conflicted with MCP SDK v2. The new `langchain.mcp` API is currently beta; dependencies are constrained and locked in `uv.lock`.

## Data and limitations

Tavily receives search queries. Prompts are local only with the default local model endpoint. Enabling optional tracing may send prompts and outputs to the tracing provider. Secrets, local databases, editor files and the original screenshot are excluded from Git.

This is a learning/portfolio project. Source URLs are requested from the model but are not independently verified. Reports can contain errors; review evidence before relying on them. Offline tests do not prove live model or search quality. Model request timeouts and workflow limits reduce runaway execution but do not guarantee successful research.
