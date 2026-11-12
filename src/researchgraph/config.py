"""Explicit startup configuration; no model or network work at import time."""

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model: str = "qwen3.5:4b"
    base_url: str = "http://localhost:11434/v1"
    max_research_rounds: int = 2

    @classmethod
    def from_environment(cls):
        load_dotenv(Path.cwd() / ".env")
        # Preserve compatibility with the original local setup; never publish this file.
        load_dotenv(Path.cwd() / "src" / ".env")
        try:
            rounds = int(os.environ.get("MAX_RESEARCH_ROUNDS", "2"))
        except ValueError as exc:
            raise ValueError(
                "MAX_RESEARCH_ROUNDS must be an integer from 1 to 5."
            ) from exc
        if not 1 <= rounds <= 5:
            raise ValueError("MAX_RESEARCH_ROUNDS must be from 1 to 5.")
        key = os.environ.get("TAVILY_API_KEY", "").strip()
        if not key or key == "replace-with-your-tavily-key":
            raise ValueError(
                "Set TAVILY_API_KEY in your environment or .env before researching."
            )
        return cls(
            os.environ.get("OLLAMA_MODEL", cls.model),
            os.environ.get("OLLAMA_BASE_URL", cls.base_url),
            rounds,
        )
