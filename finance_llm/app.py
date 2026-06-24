from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from .rag_engine import FinanceRAGEngine
from .ingestion import ingest_text
from . import config

app = FastAPI(title="Finance LLM API", version="1.0.0")
rag = FinanceRAGEngine()


class QueryRequest(BaseModel):
    question: str
    k: int = 5


class SourceInfo(BaseModel):
    content: str
    metadata: dict
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]


class IngestRequest(BaseModel):
    text: str
    source: str = "manual"
    metadata: Optional[dict] = None


class StatsResponse(BaseModel):
    document_chunks: int
    model: str


@app.get("/")
def root():
    return {"service": "Finance LLM", "status": "running"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    result = rag.query(req.question, k=req.k)
    return result


@app.post("/ingest")
def ingest_endpoint(req: IngestRequest):
    doc = ingest_text(req.text, source=req.source, metadata=req.metadata)
    rag.ingest_documents([doc])
    return {"status": "ok", "chunks_added": 1}


@app.get("/stats", response_model=StatsResponse)
def stats_endpoint():
    s = rag.get_collection_stats()
    return StatsResponse(document_chunks=s["document_chunks"], model=config.LLM_MODEL)


def serve(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)
