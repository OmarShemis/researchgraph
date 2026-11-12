"""Local SQLite notes with owner-scoped operations and closed connections."""

from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3


def database_path():
    return Path(
        os.environ.get("RESEARCHGRAPH_NOTES_DB", str(Path.cwd() / "data" / "notes.db"))
    ).expanduser()


@contextmanager
def connection():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        with conn:
            yield conn
    finally:
        conn.close()


def list_notes(owner: str) -> list[dict]:
    with connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT id, text, created_at FROM notes WHERE owner = ? ORDER BY id",
                (owner,),
            )
        ]


def add_note(owner: str, text: str) -> dict:
    text = text.strip()
    if not owner.strip() or not text or len(text) > 10000:
        raise ValueError(
            "A nonempty owner and a note of 1-10000 characters are required."
        )
    with connection() as conn:
        cursor = conn.execute(
            "INSERT INTO notes (owner, text) VALUES (?, ?)", (owner, text)
        )
        return {"id": cursor.lastrowid, "text": text}


def delete_note(owner: str, note_id: int) -> bool:
    with connection() as conn:
        return (
            conn.execute(
                "DELETE FROM notes WHERE owner = ? AND id = ?", (owner, note_id)
            ).rowcount
            > 0
        )
