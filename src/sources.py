import sys
import re
import html
import calendar
import yaml
import httpx
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Optional
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
    clean = html.unescape(clean)
    return " ".join(clean.split()).strip()

def extract_published_datetime(entry) -> Optional[datetime]:
    if getattr(entry, "published_parsed", None):
        try:
            # feedparser 提供的 published_parsed 是 UTC 9 元组，用 calendar.timegm 转换为 UTC 时间戳
            secs = calendar.timegm(entry.published_parsed)
            return datetime.fromtimestamp(secs, tz=timezone.utc)
        except Exception:
            pass
    if getattr(entry, "updated_parsed", None):
        try:
            secs = calendar.timegm(entry.updated_parsed)
            return datetime.fromtimestamp(secs, tz=timezone.utc)
        except Exception:
            pass
    return None

def is_within_max_age(pub_dt: Optional[datetime], max_age_hours: int = 36) -> bool:
    if pub_dt is None:
        # 如果源本身完全不带日期，默认保留
        return True
    now = datetime.now(timezone.utc)
    # 如果文章发布时间早于当前时间 max_age_hours 以前，视为陈旧内容过滤掉
    age_seconds = (now - pub_dt).total_seconds()
    if age_seconds > max_age_hours * 3600:
        return False
    return True

def parse_rss_content(content_bytes_or_str, source_name: str, max_items: int = 10, max_age_hours: int = 36) -> List[RawArticle]:
    feed = feedparser.parse(content_bytes_or_str)
    articles: List[RawArticle] = []
    
    for entry in feed.entries:
        if len(articles) >= max_items:
            break
            
        pub_dt = extract_published_datetime(entry)
        if not is_within_max_age(pub_dt, max_age_hours=max_age_hours):
            continue

        title = clean_html_tags(getattr(entry, "title", ""))
        url = getattr(entry, "link", "")
        summary = clean_html_tags(getattr(entry, "summary", getattr(entry, "description", "")))
        if not title or not url:
            continue
        articles.append(RawArticle(
            title=title,
            summary=summary[:300],
            url=url,
            source_name=source_name,
            published_at=pub_dt
        ))
    return articles

def load_sources_config(config_path: str = "config/sources.yaml") -> Dict[str, List[Dict]]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_feed(source_info: Dict, timeout_secs: float = 12.0, max_items: int = 10, retries: int = 2) -> List[RawArticle]:
    name = source_info.get("name", "Unknown")
    url = source_info.get("url", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*"
    }
    
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=timeout_secs, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                resp.raise_for_status()
                # 使用 resp.content 字节流让 feedparser 自主探测编码，避免多语言乱码
                return parse_rss_content(resp.content, source_name=name, max_items=max_items)
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                # 瞬时错误短暂重试
                continue
    
    safe_msg = str(last_err).encode("ascii", "replace").decode("ascii")
    print(f"[WARN] Failed to fetch feed '{name}' after {retries} attempts: {safe_msg}")
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
