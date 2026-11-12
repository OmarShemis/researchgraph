"""Local-only stdio MCP server for notes; no remote authentication layer."""

from fastmcp import FastMCP
from .notes_db import add_note, delete_note, list_notes

mcp = FastMCP(name="researchgraph-notes")


@mcp.tool()
def list_my_notes() -> list[dict]:
    """List local notes."""
    return list_notes(owner="local")


@mcp.tool()
def add_a_note(text: str) -> dict:
    """Save a local note when the user requests it."""
    return add_note(owner="local", text=text)


@mcp.tool()
def delete_a_note(note_id: int) -> str:
    """Delete a local note by id only when explicitly requested."""
    return "deleted" if delete_note(owner="local", note_id=note_id) else "not found"


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
