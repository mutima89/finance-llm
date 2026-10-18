import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    # Values already set in the environment (e.g. by Docker) take precedence.
    load_dotenv(BASE_DIR / ".env", override=False)
except ImportError:
    pass

DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma_db"

LLM_PROVIDER = os.getenv("FINANCE_LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# For Ollama, OLLAMA_MODEL wins, then FINANCE_LLM_MODEL, then llama3.
# For hosted providers, FINANCE_LLM_MODEL with a gpt-4o default.
if LLM_PROVIDER == "ollama":
    LLM_MODEL = os.getenv("OLLAMA_MODEL") or os.getenv("FINANCE_LLM_MODEL") or "llama3"
else:
    LLM_MODEL = os.getenv("FINANCE_LLM_MODEL", "gpt-4o")
OLLAMA_MODEL = LLM_MODEL if LLM_PROVIDER == "ollama" else os.getenv("OLLAMA_MODEL", "llama3")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "5"))

SCHEDULE_INTERVAL_HOURS = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "6"))

FINANCIAL_NEWS_RSS_FEEDS = [
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://www.ft.com/?format=rss",
    "https://www.economist.com/finance-and-economics/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://feeds.bloomberg.com/markets/news.rss",
]

SEC_EDGAR_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
# SEC asks automated clients to identify themselves with a name and contact email.
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "FinanceLLM/1.0 (admin@example.com)")
