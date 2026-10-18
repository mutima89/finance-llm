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


def _sec_get(url: str):
    import requests
    resp = requests.get(url, headers={"User-Agent": config.SEC_USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp


def _resolve_cik(ticker_or_cik: str) -> Optional[tuple]:
    """Return (cik, company_name) for a ticker symbol or numeric CIK."""
    value = ticker_or_cik.strip().upper()
    if value.isdigit():
        return int(value), ""
    data = _sec_get("https://www.sec.gov/files/company_tickers.json").json()
    for row in data.values():
        if row.get("ticker", "").upper() == value:
            return int(row["cik_str"]), row.get("title", "")
    return None


def _filing_text(html_text: str) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, "lxml")
    # Inline XBRL filings carry a hidden machine-readable header; drop it.
    for tag in soup(["script", "style", "ix:header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def ingest_sec_filing(ticker: str, filing_type: str = "10-K", count: int = 1) -> List[Dict[str, Any]]:
    """Fetch the most recent `count` filings of `filing_type` from SEC EDGAR.

    Uses SEC's JSON endpoints: ticker -> CIK lookup, the company's submissions
    index, then the primary filing document itself.
    """
    docs: List[Dict[str, Any]] = []
    try:
        resolved = _resolve_cik(ticker)
        if not resolved:
            print(f"  Unknown ticker or CIK: {ticker}")
            return docs
        cik, company = resolved

        subs = _sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
        company = company or subs.get("name", "")
        recent = subs.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])

        for i, form in enumerate(forms):
            if form != filing_type.upper():
                continue
            accession = recent["accessionNumber"][i]
            primary = recent["primaryDocument"][i]
            filed = recent["filingDate"][i]
            url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                f"{accession.replace('-', '')}/{primary}"
            )
            text = _filing_text(_sec_get(url).text)
            title = f"{company} {form} (filed {filed})".strip()
            docs.append({
                "content": f"{title}\n\n{text}",
                "metadata": {
                    "source": url,
                    "title": title,
                    "ticker": ticker.upper(),
                    "cik": cik,
                    "filing_type": form,
                    "filing_date": filed,
                    "accession_number": accession,
                    "ingested_at": datetime.datetime.now().isoformat(),
                    "type": "sec_filing",
                },
            })
            if len(docs) >= count:
                break
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
