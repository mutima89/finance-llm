import json
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from openai import OpenAI
from . import config


class FinanceRAGEngine:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.index_path = config.CHROMA_DIR / "faiss_index"
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[np.ndarray] = []
        self._load_or_init()

    def _load_or_init(self):
        meta_path = self.index_path / "meta.jsonl"
        emb_path = self.index_path / "embeddings.npy"
        if meta_path.exists() and emb_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                self.documents = [json.loads(line) for line in f if line.strip()]
            self.embeddings = list(np.load(str(emb_path)))
        else:
            self.documents = []
            self.embeddings = []

    def _persist(self):
        self.index_path.mkdir(parents=True, exist_ok=True)
        with open(self.index_path / "meta.jsonl", "w", encoding="utf-8") as f:
            for doc in self.documents:
                f.write(json.dumps(doc) + "\n")
        if self.embeddings:
            np.save(str(self.index_path / "embeddings.npy"), np.array(self.embeddings))

    def _chunk_text(self, text: str) -> List[str]:
        chunks = []
        words = text.split()
        chunk_size = config.CHUNK_SIZE // 5
        overlap = config.CHUNK_OVERLAP // 5
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks if chunks else [text]

    def _get_embedding(self, text: str) -> List[float]:
        resp = self.client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=text,
        )
        return resp.data[0].embedding

    def ingest_documents(self, docs: List[Dict[str, Any]]):
        for doc in docs:
            chunks = self._chunk_text(doc["content"])
            for chunk in chunks:
                emb = self._get_embedding(chunk)
                self.documents.append({
                    "content": chunk,
                    "metadata": doc.get("metadata", {}),
                })
                self.embeddings.append(np.array(emb))
        self._persist()

    def query(self, question: str, k: Optional[int] = None) -> dict:
        k = k or config.TOP_K
        if not self.documents:
            return self._query_llm_only(question)

        q_emb = np.array(self._get_embedding(question))
        sims = [np.dot(q_emb, e) / (np.linalg.norm(q_emb) * np.linalg.norm(e))
                for e in self.embeddings]
        top_idx = np.argsort(sims)[-k:][::-1]

        context_parts = []
        sources = []
        for idx in top_idx:
            context_parts.append(self.documents[idx]["content"])
            sources.append({
                "content": self.documents[idx]["content"][:300],
                "metadata": self.documents[idx]["metadata"],
                "relevance_score": round(float(sims[idx]), 4),
            })

        context = "\n\n".join(context_parts)
        return self._query_llm(question, context, sources)

    def _query_llm(self, question: str, context: str, sources: list) -> dict:
        system_msg = (
            "You are a senior financial analyst with 80 years of Wall Street experience. "
            "Use the provided context to answer. If context lacks relevant data, say so. "
            "Cite sources when referencing data. Be direct, precise, and data-driven."
        )
        resp = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"},
            ],
        )
        return {"answer": resp.choices[0].message.content, "sources": sources}

    def _query_llm_only(self, question: str) -> dict:
        system_msg = (
            "You are a senior financial analyst with 80 years of Wall Street experience. "
            "You have no specific context loaded, so answer based on your general knowledge. "
            "State clearly when you are giving general knowledge vs. specific data."
        )
        resp = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": question},
            ],
        )
        return {"answer": resp.choices[0].message.content, "sources": []}

    def get_collection_stats(self) -> dict:
        return {"document_chunks": len(self.documents)}
