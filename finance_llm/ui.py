import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from finance_llm.rag_engine import FinanceRAGEngine
from finance_llm.scheduler import IngestionScheduler
from finance_llm import config

st.set_page_config(
    page_title="Finance LLM",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Finance LLM")
st.caption("Your 80-Year Wall Street Veteran — RAG-powered financial analyst")

if "rag" not in st.session_state:
    st.session_state.rag = FinanceRAGEngine()
if "scheduler" not in st.session_state:
    st.session_state.scheduler = IngestionScheduler(st.session_state.rag)
    st.session_state.scheduler.start()
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Knowledge Base")
    stats = st.session_state.rag.get_collection_stats()
    st.metric("Document Chunks", stats["document_chunks"])
    st.metric("LLM Model", f"{config.LLM_PROVIDER}/{config.LLM_MODEL}")

    st.divider()
    st.header("Ingest Data")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📰 RSS Feeds", use_container_width=True):
            with st.spinner("Fetching RSS..."):
                from finance_llm.ingestion import ingest_rss_feeds
                docs = ingest_rss_feeds()
                st.session_state.rag.ingest_documents(docs)
                st.success(f"Ingested {len(docs)} items")
                st.rerun()

    with col2:
        if st.button("🔄 Run Scheduler", use_container_width=True):
            with st.spinner("Running scheduled ingestion..."):
                st.session_state.scheduler.run_once()
                st.success("Done")
                st.rerun()

    ticker = st.text_input("Stock ticker", placeholder="AAPL")
    if st.button("📊 Load Stock Data", use_container_width=True) and ticker:
        with st.spinner(f"Fetching {ticker}..."):
            from finance_llm.ingestion import ingest_yfinance_data
            doc = ingest_yfinance_data(ticker)
            if doc:
                st.session_state.rag.ingest_documents([doc])
                st.success(f"Ingested {ticker.upper()} data")
                st.rerun()

    url = st.text_input("URL", placeholder="https://...")
    if st.button("🌐 Ingest URL", use_container_width=True) and url:
        with st.spinner("Fetching URL..."):
            from finance_llm.ingestion import ingest_from_url
            doc = ingest_from_url(url)
            if doc:
                st.session_state.rag.ingest_documents([doc])
                st.success("Ingested")
                st.rerun()

    pdf_file = st.file_uploader("📄 Upload PDF", type=["pdf"])
    if pdf_file is not None:
        with st.spinner("Parsing PDF..."):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.getbuffer())
                from finance_llm.ingestion import ingest_pdf
                doc = ingest_pdf(tmp.name)
                Path(tmp.name).unlink()
            if doc:
                st.session_state.rag.ingest_documents([doc])
                st.success("PDF ingested")
                st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a financial question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            result = st.session_state.rag.query(prompt)
        st.markdown(result["answer"])
        if result["sources"]:
            with st.expander("📚 Sources"):
                for s in result["sources"]:
                    src = s["metadata"].get("title", s["metadata"].get("source", "unknown"))
                    st.write(f"- **{src}** (relevance: {s['relevance_score']})")
                    st.caption(s["content"][:200] + "...")
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
