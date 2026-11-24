import os
from dotenv import load_dotenv

load_dotenv()

def integer(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default

def number(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return default

LLM_MODE = os.getenv("LLM_MODE", "mock").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./assistant.db")
RATE_LIMIT_REQUESTS = max(1, integer("RATE_LIMIT_REQUESTS", 10))
RATE_LIMIT_WINDOW_SECONDS = max(1, integer("RATE_LIMIT_WINDOW_SECONDS", 60))
MAX_MESSAGE_CHARS = max(100, integer("MAX_MESSAGE_CHARS", 4000))
MAX_HISTORY_MESSAGES = max(0, integer("MAX_HISTORY_MESSAGES", 8))
# Configure current provider rates explicitly; zero means no cost estimate.
INPUT_COST_PER_1M = max(0.0, number("INPUT_COST_PER_1M", 0.0))
OUTPUT_COST_PER_1M = max(0.0, number("OUTPUT_COST_PER_1M", 0.0))
