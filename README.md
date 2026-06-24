<div align="center">
  <h1>📈 Finance LLM</h1>
  <p><strong>Your 80-Year Wall Street Veteran — Powered by RAG + LLM</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs">
  </p>
</div>

---

**Finance LLM** is a Retrieval-Augmented Generation (RAG) system that acts as a seasoned financial analyst. It ingests financial news, SEC filings, earnings reports, and market data — then answers questions with precision, context, and source citations.

## ✨ Features

- 🧠 **LLM-Powered** — Uses GPT-4o (or any OpenAI model) for expert-level financial reasoning
- 📚 **RAG Architecture** — Retrieves relevant context from your ingested documents before answering
- 📰 **RSS Ingestion** — Pulls the latest financial news from Bloomberg, WSJ, FT, and more
- 🌐 **Web Ingestion** — Ingest any webpage (SEC filings, earnings transcripts, analyst reports)
- 📄 **File Ingestion** — Load local text files (PDFs via conversion, reports, notes)
- 🔍 **Source Citations** — Every answer includes references and relevance scores
- 💬 **CLI & API** — Chat via terminal or integrate via FastAPI
- 📊 **Persistent Index** — Embeddings saved locally, survives restarts

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/finance-llm.git
cd finance-llm
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Ingest knowledge

```bash
# Load a financial report
python main.py ingest --file reports/q3-earnings.txt

# Scrape the latest news from RSS feeds
python main.py ingest --rss

# Ingest a specific article or SEC filing
python main.py ingest --url https://example.com/sec-filing
```

### 4. Ask questions

```bash
# One-shot query
python main.py query "What's the market outlook for Q4 2026?"

# Interactive chat mode
python main.py chat

# Check what's in your knowledge base
python main.py stats
```

### 5. Start the API server

```bash
python -c "from finance_llm.app import serve; serve()"
# → http://localhost:8000
```

Then query via HTTP:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Analyze the latest Fed rate decision"}'
```

## 📦 Project Structure

```
finance-llm/
├── main.py                  # Entry point (CLI)
├── requirements.txt          # Dependencies
├── .env.example              # API key template
├── .gitignore
├── data/
│   ├── chroma_db/            # Persistent vector index (auto-created)
│   └── documents/            # Place your source files here
└── finance_llm/
    ├── __init__.py
    ├── config.py             # Settings (model, chunk size, RSS feeds)
    ├── rag_engine.py         # Core RAG logic (embeddings, retrieval, LLM)
    ├── ingestion.py          # Data ingestion (files, URLs, RSS)
    ├── cli.py                # Typer CLI (query, ingest, chat, stats)
    └── app.py                # FastAPI server
```

## 🧠 How It Works

```
                    ┌─────────────────┐
                    │  Your Documents  │
                    │  (news, filings, │
                    │   reports, RSS)  │
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
                    │  (FAISS + numpy) │
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
          │  LLM (GPT-4o) + context + prompt    │
          │      │                              │
          │      ▼                              │
          │  Answer + Source Citations           │
          └─────────────────────────────────────┘
```

## ⚙️ Configuration

Edit `finance_llm/config.py` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `FINANCE_LLM_MODEL` | `gpt-4o` | LLM model for answers |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size (chars) |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `5` | Number of chunks retrieved |

## 🧪 Example

```
$ python main.py query "What's the Fed's current stance on rates?"

┌─────────────────────────────────────────────────────────────────┐
│  Answer                                                         │
│                                                                 │
│  Based on the latest FOMC meeting minutes ingested (June 2026), │
│  the Fed has held rates steady at 5.25-5.50% for the third      │
│  consecutive meeting. Chair Powell signaled a data-dependent    │
│  approach, noting that inflation remains above the 2% target    │
│  but is moving in the right direction. The dot plot indicates   │
│  two possible cuts in H2 2026, contingent on continued          │
│  disinflation and labor market softening.                       │
│                                                                 │
│  Sources: FOMC Minutes (Jun 2026), Powell Press Conference      │
└─────────────────────────────────────────────────────────────────┘
```

## 🗺️ Roadmap

- [ ] Multi-LLM support (Anthropic Claude, local Ollama models)
- [ ] PDF ingestion (via pypdf or similar)
- [ ] Scheduled RSS auto-ingestion (cron/background worker)
- [ ] Web UI (Streamlit or Gradio)
- [ ] Portfolio analysis module
- [ ] Sentiment analysis on ingested news

## 📄 License

MIT
