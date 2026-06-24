import time
import threading
import datetime
from . import config
from .rag_engine import FinanceRAGEngine
from .ingestion import ingest_rss_feeds


class IngestionScheduler:
    def __init__(self, rag: FinanceRAGEngine):
        self.rag = rag
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self, interval_hours: int | None = None):
        interval = interval_hours or config.SCHEDULE_INTERVAL_HOURS
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, args=(interval,), daemon=True
        )
        self._thread.start()
        print(f"[scheduler] Started — ingesting RSS every {interval}h")

    def stop(self):
        self._running = False

    def run_once(self):
        print(f"[scheduler] Running RSS ingestion at {datetime.datetime.now().isoformat()}")
        docs = ingest_rss_feeds()
        if docs:
            self.rag.ingest_documents(docs)
            print(f"[scheduler] Ingested {len(docs)} new RSS items")
        else:
            print("[scheduler] No new RSS items")

    def _loop(self, interval_hours: int):
        while self._running:
            self.run_once()
            time.sleep(interval_hours * 3600)
