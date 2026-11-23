import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", encoding="utf-8-sig")


def get_model():
    return ChatOpenAI(
        model=os.getenv("LOCAL_MODEL", "google/gemma-4-e4b"),
        base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:1235/v1"),
        api_key=os.getenv("LOCAL_API_KEY", "local"),
        use_responses_api=False,
        timeout=180,
        max_retries=1,
    )
