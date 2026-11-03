import sys
import re
import yaml
import httpx
import feedparser
from typing import List, Dict
from src.models import RawArticle

# 确保在 Windows 控制台输出 Unicode 字符时不崩溃
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def clean_html_tags(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw_html)
    return " ".join(clean.split()).strip()

def parse_rss_content(content_str: str, source_name: str, max_items: int = 10) -> List[RawArticle]:
    feed = feedparser.parse(content_str)
    articles: List[RawArticle] = []
    
    for entry in feed.entries[:max_items]:
        title = clean_html_tags(getattr(entry, "title", ""))
        url = getattr(entry, "link", "")
        summary = clean_html_tags(getattr(entry, "summary", getattr(entry, "description", "")))
        if not title or not url:
            continue
        articles.append(RawArticle(
            title=title,
            summary=summary[:300],
            url=url,
            source_name=source_name
        ))
    return articles

def load_sources_config(config_path: str = "config/sources.yaml") -> Dict[str, List[Dict]]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_feed(source_info: Dict, timeout_secs: float = 12.0, max_items: int = 10) -> List[RawArticle]:
    name = source_info.get("name", "Unknown")
    url = source_info.get("url", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*"
    }
    try:
        with httpx.Client(timeout=timeout_secs, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return parse_rss_content(resp.text, source_name=name, max_items=max_items)
    except Exception as exc:
        safe_msg = str(exc).encode("ascii", "replace").decode("ascii")
        print(f"[WARN] Failed to fetch feed '{name}': {safe_msg}")
        return []

def fetch_all_categories(config_path: str = "config/sources.yaml") -> Dict[str, List[RawArticle]]:
    config = load_sources_config(config_path)
    results: Dict[str, List[RawArticle]] = {}
    
    for category, sources in config.items():
        category_articles: List[RawArticle] = []
        for src in sources:
            category_articles.extend(fetch_feed(src))
        results[category] = category_articles
    return results
