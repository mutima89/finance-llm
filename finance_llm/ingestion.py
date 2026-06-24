import datetime
from typing import List, Optional, Dict, Any
from . import config


def ingest_text(text: str, source: str, metadata: Optional[dict] = None) -> Dict[str, Any]:
    meta = {
        "source": source,
        "ingested_at": datetime.datetime.now().isoformat(),
        "type": "text",
    }
    if metadata:
        meta.update(metadata)
    return {"content": text, "metadata": meta}


def ingest_from_url(url: str, title: str = "") -> Optional[Dict[str, Any]]:
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return {
            "content": text,
            "metadata": {
                "source": url,
                "title": title or (soup.title.string if soup.title else url),
                "ingested_at": datetime.datetime.now().isoformat(),
                "type": "webpage",
            },
        }
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}")
        return None


def ingest_rss_feeds(feeds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    import feedparser
    feeds = feeds or config.FINANCIAL_NEWS_RSS_FEEDS
    docs = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                content = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                title = entry.get("title", "")
                if content and link:
                    docs.append({
                        "content": f"{title}\n\n{content}",
                        "metadata": {
                            "source": link,
                            "title": title,
                            "published": entry.get("published", ""),
                            "ingested_at": datetime.datetime.now().isoformat(),
                            "type": "rss",
                            "feed": feed_url,
                        },
                    })
        except Exception as e:
            print(f"  Failed to parse feed {feed_url}: {e}")
    return docs
