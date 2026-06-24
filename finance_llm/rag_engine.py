import json
import numpy as np
from typing import List, Optional, Dict, Any, Callable
from . import config


class LLMClient:
    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.model = config.LLM_MODEL

    def _build_system_prompt(self, context: str = "") -> str:
        base = (
            "You are a senior financial analyst with 80 years of Wall Street experience. "
            "Be direct, precise, and data-driven. Avoid hype. When discussing numbers, "
            "provide context (e.g., 'compared to last quarter'). Cite sources when possible."
        )
        if context:
            base += (
                "\n\nUse the provided context to answer. If context lacks relevant data, "
                "say so clearly."
            )
        return base

    def chat(self, system: str, user: str) -> str:
        if self.provider == "anthropic":
            return self._chat_anthropic(system, user)
        elif self.provider == "ollama":
            return self._chat_ollama(system, user)
        return self._chat_openai(system, user)

    def _chat_openai(self, system: str, user: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=self.model, temperature=0.1,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content

    def _chat_anthropic(self, system: str, user: str) -> str:
        from anthropic import Anthropic
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=self.model, max_tokens=4096, temperature=0.1,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text

    def _chat_ollama(self, system: str, user: str) -> str:
        import httpx
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0.1},
        }
        resp = httpx.post(
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json=payload, timeout=120,
        )
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        content = ""
        for line in lines:
            import json as j
            try:
                content += j.loads(line).get("message", {}).get("content", "")
            except Exception:
                pass
        return content


class EmbeddingClient:
    def __init__(self):
        self.provider = config.EMBEDDING_PROVIDER
        self.model = config.EMBEDDING_MODEL

    def embed(self, text: str) -> List[float]:
        if self.provider == "ollama":
            return self._embed_ollama(text)
        return self._embed_openai(text)

    def _embed_openai(self, text: str) -> List[float]:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.embeddings.create(model=self.model, input=text)
        return resp.data[0].embedding

    def _embed_ollama(self, text: str) -> List[float]:
        import httpx
        resp = httpx.post(
            f"{config.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


class FinanceRAGEngine:
    def __init__(self):
        self.llm = LLMClient()
        self.embedder = EmbeddingClient()
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

    def ingest_documents(self, docs: List[Dict[str, Any]]):
        for doc in docs:
            chunks = self._chunk_text(doc["content"])
            for chunk in chunks:
                emb = self.embedder.embed(chunk)
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

        q_emb = np.array(self.embedder.embed(question))
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
        system = self.llm._build_system_prompt(context)
        user = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        answer = self.llm.chat(system=system, user=user)
        return {"answer": answer, "sources": sources}

    def _query_llm_only(self, question: str) -> dict:
        system = self.llm._build_system_prompt()
        user = question
        answer = self.llm.chat(system=system, user=user)
        return {"answer": answer, "sources": []}

    def get_collection_stats(self) -> dict:
        return {"document_chunks": len(self.documents)}
