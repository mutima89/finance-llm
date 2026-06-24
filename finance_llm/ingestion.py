import datetime
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
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


def ingest_pdf(file_path: str) -> Optional[Dict[str, Any]]:
    try:
        import pypdf
        path = Path(file_path)
        reader = pypdf.PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return {
            "content": text,
            "metadata": {
                "source": str(path),
                "title": path.stem,
                "pages": len(reader.pages),
                "ingested_at": datetime.datetime.now().isoformat(),
                "type": "pdf",
            },
        }
    except ImportError:
        print("  pypdf not installed. Run: pip install pypdf")
        return None
    except Exception as e:
        print(f"  Failed to parse PDF {file_path}: {e}")
        return None


def ingest_sec_filing(ticker: str, filing_type: str = "10-K", count: int = 1) -> List[Dict[str, Any]]:
    import requests
    from bs4 import BeautifulSoup
    docs = []
    try:
        params = {
            "action": "getcompany",
            "CIK": ticker,
            "type": filing_type,
            "dateb": "",
            "owner": "exclude",
            "start": "",
            "output": "atom",
            "count": count,
        }
        headers = {"User-Agent": "FinanceLLM/1.0 (contact@example.com)"}
        resp = requests.get(
            "https://www.sec.gov/cgi-bin/browse-edgar",
            params=params, headers=headers, timeout=15,
        )
        resp.raise_for_status()
        feed = resp.json()
        for entry in feed.get("feed", {}).get("entry", []):
            summary = entry.get("summary", {}).get("_value", "")
            link = ""
            for lnk in entry.get("link", []):
                if lnk.get("rel") == "alternate":
                    link = lnk.get("href", "")
                    break
            title = entry.get("title", {}).get("_value", "")
            docs.append({
                "content": f"{title}\n\n{summary}",
                "metadata": {
                    "source": link,
                    "title": title,
                    "ticker": ticker.upper(),
                    "filing_type": filing_type,
                    "ingested_at": datetime.datetime.now().isoformat(),
                    "type": "sec_filing",
                },
            })
    except Exception as e:
        print(f"  Failed to fetch SEC filing for {ticker}: {e}")
    return docs


def ingest_yfinance_data(ticker: str) -> Optional[Dict[str, Any]]:
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        content = json.dumps(info, indent=2, default=str)
        return {
            "content": content,
            "metadata": {
                "source": f"yfinance:{ticker}",
                "title": f"{ticker.upper()} - {info.get('longName', '')}",
                "ticker": ticker.upper(),
                "ingested_at": datetime.datetime.now().isoformat(),
                "type": "yfinance",
            },
        }
    except ImportError:
        print("  yfinance not installed. Run: pip install yfinance")
        return None
    except Exception as e:
        print(f"  Failed to fetch yfinance data for {ticker}: {e}")
        return None
