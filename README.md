<div align="center">
  <h1>📈 Finance LLM</h1>
  <p><strong>Your 80-Year Wall Street Veteran — Powered by RAG + LLM</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs">
    <img src="https://img.shields.io/badge/LLM-OpenAI%20%7C%20Anthropic%20%7C%20Ollama-orange" alt="Multi-LLM">
  </p>
</div>

---

**Finance LLM** is a Retrieval-Augmented Generation (RAG) system that acts as a seasoned financial analyst. It ingests financial news, SEC filings, earnings reports, stock data, and PDFs — then answers questions with precision, context, and source citations.

## ✨ Features

- 🧠 **Multi-LLM Support** — OpenAI GPT-4o, Anthropic Claude, or local Ollama models
- 📚 **RAG Architecture** — Retrieves relevant context from ingested documents before answering
- 📰 **RSS Ingestion** — Pulls latest news from Bloomberg, WSJ, FT, Economist
- 🌐 **Web Ingestion** — Scrape any webpage (SEC filings, earnings transcripts)
- 📄 **PDF Ingestion** — Parse earnings reports, whitepapers, research PDFs
- 📊 **Stock Data** — Pull live company data via yfinance
- 🏛️ **SEC Filings** — Fetch 10-K, 10-Q, 8-K filings directly from EDGAR
- 🔍 **Source Citations** — Every answer includes references with relevance scores
- 💬 **CLI & API & Web UI** — Terminal, FastAPI, and Streamlit interfaces
- ⏰ **Auto-Scheduler** — Background RSS ingestion at configurable intervals
- 📊 **Persistent Index** — Embeddings saved locally, survives restarts
- 🧪 **Evaluation Suite** — Built-in QA pairs to measure retrieval quality

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/mutima89/finance-llm.git
cd finance-llm
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (or ANTHROPIC_API_KEY)
```

### 3. Ingest knowledge

```bash
# Latest financial news
python main.py ingest --rss

# PDF earnings report
python main.py ingest --pdf reports/q3-earnings.pdf

# Stock data
python main.py ingest --ticker AAPL

# SEC filing
python main.py ingest --sec MSFT --sec-type 10-K

# Web article
python main.py ingest --url https://example.com/analysis
```

### 4. Ask questions

```bash
# One-shot query
python main.py query "What's the market outlook for Q4 2026?"

# Interactive chat mode
python main.py chat

# Check your knowledge base
python main.py stats
```

### 5. Launch the Web UI

```bash
python main.py ui
# → http://localhost:8501
```

### 6. Start the API server

```bash
python -c "from finance_llm.app import serve; serve()"
# → http://localhost:8000

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Analyze the latest Fed rate decision"}'
```

## 🖥️ Interfaces

| Interface | Command | URL |
|-----------|---------|-----|
| **CLI** | `python main.py query/ingest/chat` | Terminal |
| **Web UI** | `python main.py ui` | `http://localhost:8501` |
| **REST API** | `python -c "from finance_llm.app import serve; serve()"` | `http://localhost:8000` |

## 🔄 Multi-LLM Support

Switch providers via `.env`:

```env
# OpenAI (default)
FINANCE_LLM_PROVIDER=openai
FINANCE_LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Anthropic Claude
FINANCE_LLM_PROVIDER=anthropic
FINANCE_LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...

# Local with Ollama
FINANCE_LLM_PROVIDER=ollama
FINANCE_LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

Embeddings can also be configured independently:
```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
```

## 📦 Project Structure

```
finance-llm/
├── main.py                    # Entry point (CLI)
├── requirements.txt           # Dependencies
├── Dockerfile                 # Docker image
├── docker-compose.yml         # Multi-service (API + UI)
├── .env.example               # API key template
├── .gitignore
├── data/
│   ├── chroma_db/             # Persistent vector index (auto-created)
│   └── documents/             # Place your source files here
└── finance_llm/
    ├── __init__.py
    ├── config.py              # Settings (model, chunk size, RSS feeds)
    ├── rag_engine.py          # Core RAG (multi-LLM, embeddings, retrieval)
    ├── ingestion.py           # Data ingestion (text, PDF, URLs, RSS, SEC, yfinance)
    ├── cli.py                 # Typer CLI (query, ingest, chat, stats, schedule, evaluate, ui)
    ├── app.py                 # FastAPI REST server
    ├── ui.py                  # Streamlit web interface
    ├── scheduler.py           # Background RSS ingestion scheduler
    └── evaluate.py            # RAG evaluation suite
```

## 🧠 How It Works

```
                    ┌─────────────────┐
                    │  Your Documents  │
                    │  (news, PDFs,    │
                    │   SEC, stock,    │
                    │   RSS, web)      │
                    └────────┬────────┘
                             │ ingest
                             ▼
                    ┌─────────────────┐
                    │  Text Splitter   │
                    │  → chunks        │
                    └────────┬────────┘
                             │ embed
                             ▼
                    ┌─────────────────┐
                    │  Vector Index    │
                    │  (numpy + cosine)│
                    └────────┬────────┘
                             │ retrieve
          ┌──────────────────┴──────────────────┐
          │  User Question                      │
          │      │                              │
          │      ▼                              │
          │  Embed question → cosine sim        │
          │  → top-k chunks + context           │
          │      │                              │
          │      ▼                              │
          │  LLM (GPT-4o / Claude / Ollama)     │
          │  + context + prompt                 │
          │      │                              │
          │      ▼                              │
          │  Answer + Source Citations           │
          └─────────────────────────────────────┘
```

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FINANCE_LLM_PROVIDER` | `openai` | LLM provider (`openai`, `anthropic`, `ollama`) |
| `FINANCE_LLM_MODEL` | `gpt-4o` | Model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `EMBEDDING_PROVIDER` | `openai` | Embedding provider |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size (chars) |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `5` | Number of chunks retrieved |
| `SCHEDULE_INTERVAL_HOURS` | `6` | Auto-ingestion interval |

## 🐳 Docker Deployment

```bash
# Build and run everything
docker compose up -d

# Or just the API
docker build -t finance-llm .
docker run -p 8000:8000 --env-file .env -v ./data:/app/data finance-llm
```

## 🧪 Evaluation

```bash
python main.py evaluate
```

Runs 5 built-in QA pairs and reports retrieval accuracy. Results saved to `eval_report.json`.

Example output:
```
============================================================
  RAG Evaluation Report
============================================================
  Total questions: 5
  Passed:          4
  Failed:          1
  Accuracy:        80.0%
============================================================

✅ What is the current federal funds rate...
   Topics found:   federal funds rate, FOMC, Fed
   Has sources:    True
...
```

## 🧩 Example

```
$ python main.py query "What's the Fed's current stance on rates?"

┌─────────────────────────────────────────────────────────────────┐
│  Answer                                                         │
│                                                                 │
│  Based on the latest FOMC meeting minutes ingested (June 2026), │
│  the Fed has held rates steady at 5.25-5.50% for the third      │
│  consecutive meeting. Chair Powell signaled a data-dependent    │
│  approach...                                                    │
│                                                                 │
│  Sources: FOMC Minutes (Jun 2026), Powell Press Conference      │
└─────────────────────────────────────────────────────────────────┘
```

## 📄 License

MIT
