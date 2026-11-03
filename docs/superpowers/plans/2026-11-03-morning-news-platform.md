# 个人早报自动化平台 (Morning News Platform) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个全自动化的个人早报生成与分发平台，每日抓取欧美主流财经、国际要闻与芬兰北欧新闻，经 LLM 智能提炼为结构化晨报，并通过邮件 Newsletter 与 GitHub Pages 静态网站双模发布。

**Architecture:** 纯 Python 流水线设计，由 GitHub Actions 定时触发。数据经过数据抓取层 (`sources.py`) -> AI 核心处理层 (`llm_pipeline.py`) -> 排版渲染层 (`renderer.py`) -> 邮件触达 (`notifier.py`) 与 Web 静态归档发布，各模块高度解耦。

**Tech Stack:** Python 3.11+, `httpx`, `feedparser`, `pydantic`, `openai`, `jinja2`, `premailer`, `pyyaml`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-03-morning-news-platform-design.md`

## Global Constraints

- Python 版本要求：>= 3.11
- 严格遵循类型标注与 Pydantic V2 数据模型校验
- 纯内联 CSS 邮件渲染，杜绝任何外部样式表引用
- 无中国大陆境内新闻源，全部使用欧美及亚太主流国际源与芬兰官方源
- 密码密钥绝对不硬编码，通过环境变量与 GitHub Secrets 统一读取

---

### Task 1: 项目基础结构、依赖配置与 Pydantic 数据模型

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `src/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces:
  - `RawArticle(title: str, summary: str, url: str, source_name: str, published_at: Optional[datetime])`
  - `NewsItem(title: str, summary: str, impact: str, source_name: str, url: str)`
  - `MorningDigest(date_str: str, headline_quote: str, macro_markets: list[NewsItem], global_affairs: list[NewsItem], finland_nordic: list[NewsItem], quick_bites: list[str])`

- [ ] **Step 1: 创建基础配置与依赖文件**

```bash
# requirements.txt
httpx>=0.27.0
feedparser>=6.0.11
pydantic>=2.7.0
openai>=1.25.0
jinja2>=3.1.3
premailer>=3.10.0
pyyaml>=6.0.1
python-dotenv>=1.0.1
pytest>=8.1.0
pytest-asyncio>=0.23.6
```

- [ ] **Step 2: 创建 `.gitignore` 与 `.env.example`**

```gitignore
# .gitignore
__pycache__/
*.py[cod]
.env
.venv/
venv/
.pytest_cache/
public/data/*.json
public/archive/*.html
!public/archive/.gitkeep
```

```bash
# .env.example
LLM_API_KEY=sk-your-llm-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
RECEIVER_EMAIL=your-email@gmail.com

SITE_URL=https://username.github.io/morningnews
```

- [ ] **Step 3: 编写数据模型的失败测试**

```python
# tests/test_models.py
from src.models import RawArticle, NewsItem, MorningDigest

def test_raw_article_model():
    article = RawArticle(
        title="Fed Signals Rate Path",
        summary="Federal Reserve maintains cautious stance.",
        url="https://wsj.com/article/1",
        source_name="Wall Street Journal"
    )
    assert article.title == "Fed Signals Rate Path"
    assert article.source_name == "Wall Street Journal"

def test_morning_digest_validation():
    item = NewsItem(
        title="美联储释放降息路径信号",
        summary="美联储最新声明重申对通胀回落的耐心。",
        impact="美债收益率小幅下行，市场情绪平稳。",
        source_name="WSJ",
        url="https://wsj.com/article/1"
    )
    digest = MorningDigest(
        date_str="2026年11月03日 星期二",
        headline_quote="全球市场静候大选与利率决议落地",
        macro_markets=[item],
        global_affairs=[item],
        finland_nordic=[item],
        quick_bites=["芬兰第三季度GDP环比微增0.2%"]
    )
    assert len(digest.macro_markets) == 1
    assert digest.quick_bites[0] == "芬兰第三季度GDP环比微增0.2%"
```

- [ ] **Step 4: 运行测试验证失败**

Run: `pytest tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.models')

- [ ] **Step 5: 编写 `src/models.py` 最小实现**

```python
# src/models.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class RawArticle(BaseModel):
    title: str
    summary: str
    url: str
    source_name: str
    published_at: Optional[datetime] = None

class NewsItem(BaseModel):
    title: str = Field(description="中文提炼标题")
    summary: str = Field(description="2-3 句中文核心事件经过")
    impact: str = Field(description="深度解读 / 商业市场影响 / 后续看点")
    source_name: str = Field(description="原媒体名称")
    url: str = Field(description="原文链接")

class MorningDigest(BaseModel):
    date_str: str = Field(description="格式：YYYY年MM月DD日 星期X")
    headline_quote: str = Field(description="今日晨报宏观脉搏一句话金句")
    macro_markets: List[NewsItem] = Field(default_factory=list, description="欧美财经与商业要闻")
    global_affairs: List[NewsItem] = Field(default_factory=list, description="国际重要焦点事件")
    finland_nordic: List[NewsItem] = Field(default_factory=list, description="芬兰本地与北欧观察")
    quick_bites: List[str] = Field(default_factory=list, description="3-5条 一句话速览短快讯")
```

- [ ] **Step 6: 运行测试验证通过**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 7: 提交代码**

```bash
git add requirements.txt .gitignore .env.example src/__init__.py src/models.py tests/test_models.py
git commit -m "feat: setup project baseline and Pydantic data models"
```

---

### Task 2: 新闻源配置与并发采集模块 (`config/sources.yaml` & `sources.py`)

**Files:**
- Create: `config/sources.yaml`
- Create: `src/sources.py`
- Test: `tests/test_sources.py`

**Interfaces:**
- Consumes:
  - `RawArticle` from `src.models`
- Produces:
  - `load_sources_config(config_path: str = "config/sources.yaml") -> dict[str, list[dict]]`
  - `fetch_feed(source_info: dict, timeout_secs: float = 10.0) -> list[RawArticle]`
  - `fetch_all_categories(config_path: str = "config/sources.yaml") -> dict[str, list[RawArticle]]`

- [ ] **Step 1: 创建 `config/sources.yaml`**

```yaml
# config/sources.yaml
finance_markets:
  - name: "Financial Times (FT)"
    url: "https://www.ft.com/rss/home/us"
  - name: "Wall Street Journal (WSJ Markets)"
    url: "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
  - name: "CNBC Top News"
    url: "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date"
  - name: "MarketWatch"
    url: "https://feeds.content.dowjones.io/public/rss/mw_topstories"

global_news:
  - name: "South China Morning Post (SCMP)"
    url: "https://www.scmp.com/rss/91/feed"
  - name: "Nikkei Asia"
    url: "https://asia.nikkei.com/rss/feed/nar"
  - name: "Reuters World"
    url: "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=best"
  - name: "BBC News World"
    url: "http://feeds.bbci.co.uk/news/world/rss.xml"
  - name: "Lianhe Zaobao (国际)"
    url: "https://www.zaobao.com.sg/rss/realtime/world"

finland_nordic:
  - name: "Yle News (芬兰广播公司)"
    url: "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_NEWS"
  - name: "Helsinki Times"
    url: "https://www.helsinkitimes.fi/finland?format=feed&type=rss"
```

- [ ] **Step 2: 编写采集模块测试（Mock 网络请求）**

```python
# tests/test_sources.py
import pytest
from src.sources import parse_rss_content, load_sources_config

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample Feed</title>
    <item>
      <title>ECB Holds Rates Steady</title>
      <link>https://example.com/ecb-rates</link>
      <description>&lt;p&gt;The ECB kept benchmark rates unchanged today.&lt;/p&gt;</description>
      <pubDate>Mon, 03 Nov 2026 08:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

def test_parse_rss_content():
    articles = parse_rss_content(SAMPLE_RSS, source_name="Test Source", max_items=5)
    assert len(articles) == 1
    assert articles[0].title == "ECB Holds Rates Steady"
    assert articles[0].url == "https://example.com/ecb-rates"
    assert "The ECB kept benchmark rates" in articles[0].summary
    assert articles[0].source_name == "Test Source"

def test_load_sources_config():
    config = load_sources_config("config/sources.yaml")
    assert "finance_markets" in config
    assert "global_news" in config
    assert "finland_nordic" in config
    assert len(config["finance_markets"]) >= 2
```

- [ ] **Step 3: 运行测试验证失败**

Run: `pytest tests/test_sources.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.sources')

- [ ] **Step 4: 编写 `src/sources.py` 实现**

```python
# src/sources.py
import re
import yaml
import httpx
import feedparser
from typing import List, Dict
from src.models import RawArticle

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

def fetch_feed(source_info: Dict, timeout_secs: float = 10.0, max_items: int = 10) -> List[RawArticle]:
    name = source_info.get("name", "Unknown")
    url = source_info.get("url", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MorningNewsBot/1.0"
    }
    try:
        with httpx.Client(timeout=timeout_secs, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return parse_rss_content(resp.text, source_name=name, max_items=max_items)
    except Exception as exc:
        print(f"[WARN] Failed to fetch feed '{name}' from {url}: {exc}")
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
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_sources.py -v`
Expected: PASS

- [ ] **Step 6: 提交代码**

```bash
git add config/sources.yaml src/sources.py tests/test_sources.py
git commit -m "feat: implement RSS sources configuration and fetcher"
```

---

### Task 3: LLM 智能提炼与数据规整管道 (`src/llm_pipeline.py`)

**Files:**
- Create: `src/llm_pipeline.py`
- Test: `tests/test_llm_pipeline.py`

**Interfaces:**
- Consumes:
  - `RawArticle`, `NewsItem`, `MorningDigest` from `src.models`
- Produces:
  - `build_llm_prompt(articles_by_cat: dict[str, list[RawArticle]], target_date_str: str) -> str`
  - `generate_morning_digest(articles_by_cat: dict[str, list[RawArticle]], target_date_str: str, client: Optional[openai.OpenAI] = None) -> MorningDigest`

- [ ] **Step 1: 编写 LLM Pipeline 测试（带 Mock Client）**

```python
# tests/test_llm_pipeline.py
import json
from unittest.mock import MagicMock
from src.models import RawArticle, MorningDigest
from src.llm_pipeline import build_llm_prompt, parse_llm_response, generate_morning_digest

def test_build_llm_prompt():
    articles = {
        "finance_markets": [
            RawArticle(title="S&P 500 Rallies", summary="Tech leads gains.", url="https://wsj.com/1", source_name="WSJ")
        ]
    }
    prompt = build_llm_prompt(articles, "2026年11月03日 星期二")
    assert "S&P 500 Rallies" in prompt
    assert "WSJ" in prompt
    assert "2026年11月03日 星期二" in prompt

def test_parse_llm_response_valid_json():
    mock_json = json.dumps({
        "date_str": "2026年11月03日 星期二",
        "headline_quote": "全球市场科技股领涨",
        "macro_markets": [{
            "title": "标普500指数因科技板块上涨",
            "summary": "标普500指数隔夜涨超1.2%，科技巨头领涨。",
            "impact": "提振了亚太早盘的风险偏好。",
            "source_name": "WSJ",
            "url": "https://wsj.com/1"
        }],
        "global_affairs": [],
        "finland_nordic": [],
        "quick_bites": ["美欧长端国债收益率微跌"]
    })
    digest = parse_llm_response(mock_json)
    assert isinstance(digest, MorningDigest)
    assert digest.headline_quote == "全球市场科技股领涨"
    assert digest.macro_markets[0].source_name == "WSJ"

def test_generate_morning_digest_with_mock_client():
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps({
            "date_str": "2026-11-03",
            "headline_quote": "早安要闻",
            "macro_markets": [],
            "global_affairs": [],
            "finland_nordic": [],
            "quick_bites": []
        })))
    ]
    mock_client.chat.completions.create.return_value = mock_completion
    
    digest = generate_morning_digest({}, "2026-11-03", client=mock_client)
    assert digest.date_str == "2026-11-03"
    assert digest.headline_quote == "早安要闻"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_llm_pipeline.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.llm_pipeline')

- [ ] **Step 3: 编写 `src/llm_pipeline.py` 实现**

```python
# src/llm_pipeline.py
import os
import json
import re
from typing import Dict, List, Optional
from openai import OpenAI
from src.models import RawArticle, MorningDigest

SYSTEM_PROMPT = """你是一位顶尖的国际宏观经济、全球要闻与北欧商业晨报总编。
你的任务是将提供的最新一手英文和国际新闻素材，精炼整理成一份高质量、高信息密度的中文早间晨报。

核心原则：
1. 真实客观：严格基于提供的素材提炼，严禁捏造未经证实的信息。
2. 专业术语精准：采用标准的财经与国际关系中文规范词汇（如 美联储利率决议、美债收益率、欧洲央行、赫尔辛基证券交易所等）。
3. 结构清晰：分为 欧美财经与全球市场、国际焦点大事、芬兰与北欧观察、一句话快讯 4 个部分。
4. 必须输出严格合法的 JSON 对象，不包含任何 Markdown 代码块标签（如 ```json ... ```），直接返回纯 JSON 字符串。
"""

def build_llm_prompt(articles_by_cat: Dict[str, List[RawArticle]], target_date_str: str) -> str:
    lines = [f"【今日晨报日期】: {target_date_str}\n", "以下是搜集到的最新原始新闻素材：\n"]
    for cat, articles in articles_by_cat.items():
        lines.append(f"### 板块: {cat}")
        for idx, art in enumerate(articles[:12], 1):
            lines.append(f"{idx}. [{art.source_name}] {art.title}")
            if art.summary:
                lines.append(f"   摘要: {art.summary}")
            lines.append(f"   链接: {art.url}")
        lines.append("")
    
    lines.append("""请基于以上素材，生成包含以下字段的 JSON 对象：
{
  "date_str": "日期字符串",
  "headline_quote": "今日核心一句话概括（晨报金句/全盘脉搏）",
  "macro_markets": [
    {
      "title": "中文核心标题",
      "summary": "2-3句中文核心事件事实",
      "impact": "深度解读/市场商业影响/后续看点",
      "source_name": "媒体名称",
      "url": "原文链接"
    }
  ],
  "global_affairs": [同上],
  "finland_nordic": [同上],
  "quick_bites": [
    "一句话简讯1",
    "一句话简讯2"
  ]
}
""")
    return "\n".join(lines)

def parse_llm_response(raw_text: str) -> MorningDigest:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)
    return MorningDigest.model_validate(data)

def generate_morning_digest(
    articles_by_cat: Dict[str, List[RawArticle]],
    target_date_str: str,
    client: Optional[OpenAI] = None
) -> MorningDigest:
    if client is None:
        api_key = os.getenv("LLM_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        model = os.getenv("LLM_MODEL", "deepseek-chat")

    prompt = build_llm_prompt(articles_by_cat, target_date_str)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    raw_content = response.choices[0].message.content or "{}"
    return parse_llm_response(raw_content)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_llm_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add src/llm_pipeline.py tests/test_llm_pipeline.py
git commit -m "feat: implement LLM structuring pipeline and prompt builder"
```

---

### Task 4: 模板排版与渲染模块 (`templates/` & `src/renderer.py`)

**Files:**
- Create: `templates/email.html.j2`
- Create: `templates/web.html.j2`
- Create: `src/renderer.py`
- Test: `tests/test_renderer.py`

**Interfaces:**
- Consumes:
  - `MorningDigest` from `src.models`
- Produces:
  - `render_email_html(digest: MorningDigest, site_url: str = "") -> str`
  - `render_web_html(digest: MorningDigest, archive_dates: list[str], site_url: str = "") -> str`
  - `save_web_artifacts(digest: MorningDigest, output_dir: str = "public", site_url: str = "") -> None`

- [ ] **Step 1: 编写模板渲染测试**

```python
# tests/test_renderer.py
import os
import shutil
from src.models import MorningDigest, NewsItem
from src.renderer import render_email_html, render_web_html, save_web_artifacts

def make_sample_digest():
    item = NewsItem(
        title="测试标题",
        summary="测试摘要内容。",
        impact="市场影响正面。",
        source_name="FT",
        url="https://ft.com"
    )
    return MorningDigest(
        date_str="2026年11月03日 星期二",
        headline_quote="测试金句一句话",
        macro_markets=[item],
        global_affairs=[item],
        finland_nordic=[item],
        quick_bites=["快讯1：测试条目"]
    )

def test_render_email_html():
    digest = make_sample_digest()
    html = render_email_html(digest, site_url="https://example.com")
    assert "测试金句一句话" in html
    assert "测试标题" in html
    assert "FT" in html
    assert "快讯1：测试条目" in html
    # 验证样式已内联，含有 style= 属性
    assert "style=" in html

def test_render_web_html():
    digest = make_sample_digest()
    html = render_web_html(digest, archive_dates=["2026-11-02", "2026-11-03"], site_url="https://example.com")
    assert "<!DOCTYPE html>" in html
    assert "测试金句一句话" in html
    assert "测试标题" in html

def test_save_web_artifacts(tmp_path):
    digest = make_sample_digest()
    out_dir = str(tmp_path / "public")
    save_web_artifacts(digest, output_dir=out_dir, site_url="https://example.com")
    
    assert os.path.exists(os.path.join(out_dir, "index.html"))
    assert os.path.exists(os.path.join(out_dir, "data", "latest.json"))
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_renderer.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.renderer')

- [ ] **Step 3: 创建 `templates/email.html.j2`**

```jinja2
<!-- templates/email.html.j2 -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>今日晨报 - {{ digest.date_str }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f6f7f9; margin: 0; padding: 20px 0; color: #1f2937; }
    .container { max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; }
    .header { background: #111827; color: #ffffff; padding: 24px; }
    .date-badge { font-size: 12px; letter-spacing: 1px; color: #9ca3af; text-transform: uppercase; margin-bottom: 6px; }
    .headline-quote { font-size: 18px; font-weight: 600; line-height: 1.4; color: #f3f4f6; margin: 0; }
    .content { padding: 24px; }
    .section-title { font-size: 15px; font-weight: 700; color: #111827; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; margin: 24px 0 16px 0; }
    .news-card { margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid #f3f4f6; }
    .news-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 6px 0; }
    .news-summary { font-size: 14px; line-height: 1.6; color: #4b5563; margin: 0 0 6px 0; }
    .news-impact { font-size: 13px; line-height: 1.5; color: #1e40af; background: #eff6ff; padding: 6px 10px; border-radius: 4px; margin: 6px 0; }
    .news-meta { font-size: 12px; color: #9ca3af; }
    .news-meta a { color: #3b82f6; text-decoration: none; }
    .quick-list { margin: 0; padding-left: 20px; font-size: 13px; color: #4b5563; line-height: 1.7; }
    .footer { background: #f9fafb; padding: 18px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; }
    .footer a { color: #3b82f6; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="date-badge">MORNING BRIEFING · {{ digest.date_str }}</div>
      <p class="headline-quote">“{{ digest.headline_quote }}”</p>
    </div>
    <div class="content">
      {% if digest.macro_markets %}
      <div class="section-title">📊 欧美财经与宏观市场</div>
      {% for item in digest.macro_markets %}
      <div class="news-card">
        <h3 class="news-title">{{ item.title }}</h3>
        <p class="news-summary">{{ item.summary }}</p>
        <div class="news-impact">💡 <strong>看点：</strong>{{ item.impact }}</div>
        <div class="news-meta">来源: <a href="{{ item.url }}" target="_blank">{{ item.source_name }} ↗</a></div>
      </div>
      {% endfor %}
      {% endif %}

      {% if digest.global_affairs %}
      <div class="section-title">🌍 国际焦点与综合要闻</div>
      {% for item in digest.global_affairs %}
      <div class="news-card">
        <h3 class="news-title">{{ item.title }}</h3>
        <p class="news-summary">{{ item.summary }}</p>
        <div class="news-impact">💡 <strong>看点：</strong>{{ item.impact }}</div>
        <div class="news-meta">来源: <a href="{{ item.url }}" target="_blank">{{ item.source_name }} ↗</a></div>
      </div>
      {% endfor %}
      {% endif %}

      {% if digest.finland_nordic %}
      <div class="section-title">🇫🇮 芬兰与北欧观察</div>
      {% for item in digest.finland_nordic %}
      <div class="news-card">
        <h3 class="news-title">{{ item.title }}</h3>
        <p class="news-summary">{{ item.summary }}</p>
        <div class="news-impact">💡 <strong>看点：</strong>{{ item.impact }}</div>
        <div class="news-meta">来源: <a href="{{ item.url }}" target="_blank">{{ item.source_name }} ↗</a></div>
      </div>
      {% endfor %}
      {% endif %}

      {% if digest.quick_bites %}
      <div class="section-title">⚡ 一句话快讯速览</div>
      <ul class="quick-list">
        {% for bite in digest.quick_bites %}
        <li>{{ bite }}</li>
        {% endfor %}
      </ul>
      {% endif %}
    </div>
    <div class="footer">
      本早报由个人自动化流水线自动生成 · <a href="{{ site_url }}" target="_blank">在线 Web 仪表盘与往期归档 ↗</a>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 4: 创建 `templates/web.html.j2`**

```jinja2
<!-- templates/web.html.j2 -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>今日晨报 · {{ digest.date_str }}</title>
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --primary: #2563eb;
      --badge-bg: #eff6ff;
      --badge-text: #1d4ed8;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0b0f19;
        --card-bg: #111827;
        --text: #f8fafc;
        --text-muted: #94a3b8;
        --border: #1f2937;
        --primary: #3b82f6;
        --badge-bg: #1e293b;
        --badge-text: #60a5fa;
      }
    }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 24px 16px; line-height: 1.6; }
    .wrapper { max-width: 760px; margin: 0 auto; }
    header { margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
    .badge { font-size: 13px; font-weight: 600; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; }
    h1 { font-size: 26px; margin: 8px 0; font-weight: 700; line-height: 1.3; }
    .quote-box { background: var(--card-bg); border-left: 4px solid var(--primary); border: 1px solid var(--border); border-left-width: 4px; padding: 14px 18px; border-radius: 6px; font-size: 16px; font-weight: 500; margin: 16px 0; }
    .section-title { font-size: 18px; font-weight: 700; margin: 28px 0 16px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin-bottom: 14px; }
    .card-title { font-size: 16px; font-weight: 600; margin: 0 0 8px; }
    .card-desc { font-size: 14px; color: var(--text-muted); margin: 0 0 10px; }
    .card-impact { font-size: 13px; background: var(--badge-bg); color: var(--badge-text); padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; }
    .card-meta a { font-size: 12px; color: var(--primary); text-decoration: none; font-weight: 500; }
    .card-meta a:hover { text-decoration: underline; }
    .quick-bites-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px 20px; }
    .quick-bites-box ul { margin: 0; padding-left: 20px; }
    .quick-bites-box li { margin-bottom: 8px; font-size: 14px; color: var(--text-muted); }
    footer { margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border); text-align: center; font-size: 13px; color: var(--text-muted); }
  </style>
</head>
<body>
  <div class="wrapper">
    <header>
      <div class="badge">早报仪表盘 · {{ digest.date_str }}</div>
      <div class="quote-box">“{{ digest.headline_quote }}”</div>
    </header>

    {% if digest.macro_markets %}
    <div class="section-title">📊 欧美财经与宏观商业</div>
    {% for item in digest.macro_markets %}
    <div class="card">
      <div class="card-title">{{ item.title }}</div>
      <div class="card-desc">{{ item.summary }}</div>
      <div class="card-impact">💡 <strong>看点：</strong>{{ item.impact }}</div>
      <div class="card-meta"><a href="{{ item.url }}" target="_blank">来源: {{ item.source_name }} ↗</a></div>
    </div>
    {% endfor %}
    {% endif %}

    {% if digest.global_affairs %}
    <div class="section-title">🌍 国际焦点与大事</div>
    {% for item in digest.global_affairs %}
    <div class="card">
      <div class="card-title">{{ item.title }}</div>
      <div class="card-desc">{{ item.summary }}</div>
      <div class="card-impact">💡 <strong>看点：</strong>{{ item.impact }}</div>
      <div class="card-meta"><a href="{{ item.url }}" target="_blank">来源: {{ item.source_name }} ↗</a></div>
    </div>
    {% endfor %}
    {% endif %}

    {% if digest.finland_nordic %}
    <div class="section-title">🇫🇮 芬兰与北欧观察</div>
    {% for item in digest.finland_nordic %}
    <div class="card">
      <div class="card-title">{{ item.title }}</div>
      <div class="card-desc">{{ item.summary }}</div>
      <div class="card-impact">💡 <strong>看点：</strong>{{ item.impact }}</div>
      <div class="card-meta"><a href="{{ item.url }}" target="_blank">来源: {{ item.source_name }} ↗</a></div>
    </div>
    {% endfor %}
    {% endif %}

    {% if digest.quick_bites %}
    <div class="section-title">⚡ 一句话快讯</div>
    <div class="quick-bites-box">
      <ul>
        {% for b in digest.quick_bites %}
        <li>{{ b }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    <footer>
      个人早报平台 · 每天自动更新
    </footer>
  </div>
</body>
</html>
```

- [ ] **Step 5: 编写 `src/renderer.py` 实现**

```python
# src/renderer.py
import os
import json
from datetime import datetime
from typing import List
from jinja2 import Environment, FileSystemLoader
from premailer import transform
from src.models import MorningDigest

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

def get_jinja_env() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

def render_email_html(digest: MorningDigest, site_url: str = "") -> str:
    env = get_jinja_env()
    tmpl = env.get_template("email.html.j2")
    raw_html = tmpl.render(digest=digest, site_url=site_url)
    # 使用 premailer 将 CSS 内联化，彻底适配所有邮件客户端
    return transform(raw_html)

def render_web_html(digest: MorningDigest, archive_dates: List[str], site_url: str = "") -> str:
    env = get_jinja_env()
    tmpl = env.get_template("web.html.j2")
    return tmpl.render(digest=digest, archive_dates=archive_dates, site_url=site_url)

def save_web_artifacts(digest: MorningDigest, output_dir: str = "public", site_url: str = "") -> None:
    os.makedirs(output_dir, exist_ok=True)
    archive_dir = os.path.join(output_dir, "archive")
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 渲染当前主页 index.html
    index_html = render_web_html(digest, archive_dates=[today_str], site_url=site_url)
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # 渲染归档页
    archive_path = os.path.join(archive_dir, f"{today_str}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    # 存最新 JSON 数据备份
    json_path = os.path.join(data_dir, "latest.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(digest.model_dump_json(indent=2))
```

- [ ] **Step 6: 运行测试验证通过**

Run: `pytest tests/test_renderer.py -v`
Expected: PASS

- [ ] **Step 7: 提交代码**

```bash
git add templates/ src/renderer.py tests/test_renderer.py
git commit -m "feat: implement Jinja2 templates and email/web renderer"
```

---

### Task 5: 邮件推送模块 (`src/notifier.py`)

**Files:**
- Create: `src/notifier.py`
- Test: `tests/test_notifier.py`

**Interfaces:**
- Produces:
  - `send_email(subject: str, html_content: str, config: Optional[dict] = None) -> bool`

- [ ] **Step 1: 编写邮件发送器测试（Mock SMTP）**

```python
# tests/test_notifier.py
from unittest.mock import patch, MagicMock
from src.notifier import send_email

def test_send_email_ssl_success():
    config = {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": 465,
        "SMTP_USER": "test@gmail.com",
        "SMTP_PASS": "mock-pass",
        "RECEIVER_EMAIL": "receiver@gmail.com"
    }
    with patch("smtplib.SMTP_SSL") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instance
        
        ok = send_email("今日早报", "<p>Hello</p>", config=config)
        assert ok is True
        instance.login.assert_called_once_with("test@gmail.com", "mock-pass")
        instance.send_message.assert_called_once()

def test_send_email_missing_config():
    # 缺失配置时返回 False，不崩溃
    ok = send_email("今日早报", "<p>Hello</p>", config={})
    assert ok is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_notifier.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.notifier')

- [ ] **Step 3: 编写 `src/notifier.py` 实现**

```python
# src/notifier.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional

def send_email(subject: str, html_content: str, config: Optional[Dict[str, str]] = None) -> bool:
    if config is None:
        config = {
            "SMTP_HOST": os.getenv("SMTP_HOST", ""),
            "SMTP_PORT": os.getenv("SMTP_PORT", "465"),
            "SMTP_USER": os.getenv("SMTP_USER", ""),
            "SMTP_PASS": os.getenv("SMTP_PASS", ""),
            "RECEIVER_EMAIL": os.getenv("RECEIVER_EMAIL", "")
        }
    
    host = config.get("SMTP_HOST", "").strip()
    port = int(config.get("SMTP_PORT", 465))
    user = config.get("SMTP_USER", "").strip()
    pwd = config.get("SMTP_PASS", "").strip()
    receiver = config.get("RECEIVER_EMAIL", "").strip()

    if not all([host, user, pwd, receiver]):
        print("[WARN] SMTP configuration is incomplete. Skipping email sending.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Morning Briefing <{user}>"
    msg["To"] = receiver
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15.0) as server:
                server.login(user, pwd)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15.0) as server:
                server.starttls()
                server.login(user, pwd)
                server.send_message(msg)
        print(f"[INFO] Morning news email sent successfully to {receiver}")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to send email via SMTP: {exc}")
        return False
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_notifier.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add src/notifier.py tests/test_notifier.py
git commit -m "feat: implement SMTP email notifier with TLS/SSL support"
```

---

### Task 6: 主程序编排与 CLI 驱动 (`src/main.py`)

**Files:**
- Create: `src/main.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Produces:
  - CLI commands:
    - `python src/main.py --dry-run` (抓取、生成、渲染但不出真实邮件)
    - `python src/main.py --no-email` (生成并保存 Web 产物，跳过发信)
    - `python src/main.py --test-sources` (仅测试 RSS 连通性)

- [ ] **Step 1: 编写 CLI 入口测试**

```python
# tests/test_main.py
from unittest.mock import patch, MagicMock
from src.main import run_pipeline

@patch("src.main.fetch_all_categories")
@patch("src.main.generate_morning_digest")
@patch("src.main.save_web_artifacts")
@patch("src.main.send_email")
def test_run_pipeline_dry_run(mock_send, mock_save, mock_digest, mock_fetch):
    mock_fetch.return_value = {"finance_markets": []}
    mock_digest.return_value = MagicMock(headline_quote="测试", date_str="2026-11-03")
    
    code = run_pipeline(dry_run=True, no_email=False, test_sources=False)
    assert code == 0
    mock_fetch.assert_called_once()
    mock_digest.assert_called_once()
    mock_save.assert_called_once()
    # dry-run 状态下不应该真正发信
    mock_send.assert_not_called()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_main.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.main')

- [ ] **Step 3: 编写 `src/main.py` 实现**

```python
# src/main.py
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

from src.sources import fetch_all_categories, load_sources_config, fetch_feed
from src.llm_pipeline import generate_morning_digest
from src.renderer import render_email_html, save_web_artifacts
from src.notifier import send_email

load_dotenv()

def get_current_date_str() -> str:
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    now = datetime.now()
    return f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]}"

def run_pipeline(dry_run: bool = False, no_email: bool = False, test_sources: bool = False) -> int:
    if test_sources:
        print("[INFO] Testing sources connectivity...")
        config = load_sources_config()
        total_items = 0
        for cat, sources in config.items():
            print(f"\n--- Checking category: {cat} ---")
            for s in sources:
                articles = fetch_feed(s, max_items=5)
                print(f"[{s['name']}] fetched {len(articles)} items.")
                total_items += len(articles)
        print(f"\n[DONE] Finished sources check, total valid articles: {total_items}")
        return 0

    date_str = get_current_date_str()
    print(f"[INFO] Starting Morning News pipeline for {date_str}...")

    # 1. 抓取所有源
    print("[1/4] Fetching news from RSS feeds...")
    articles_by_cat = fetch_all_categories()
    total_fetched = sum(len(v) for v in articles_by_cat.values())
    print(f"      Total fetched: {total_fetched} raw articles across {len(articles_by_cat)} categories.")

    # 2. LLM 提炼
    print("[2/4] Processing through LLM pipeline...")
    digest = generate_morning_digest(articles_by_cat, target_date_str=date_str)
    print(f"      LLM Digest generated: '{digest.headline_quote}'")

    # 3. 渲染并保存 Web 产物
    site_url = os.getenv("SITE_URL", "")
    print("[3/4] Rendering Web dashboard and saving artifacts to public/...")
    save_web_artifacts(digest, output_dir="public", site_url=site_url)

    # 4. 邮件推送
    if dry_run or no_email:
        print("[4/4] Email sending skipped (--dry-run or --no-email flag active).")
    else:
        print("[4/4] Rendering email and dispatching via SMTP...")
        email_html = render_email_html(digest, site_url=site_url)
        subject = f"今日早报 · {digest.headline_quote} ({digest.date_str})"
        send_email(subject, email_html)

    print("[SUCCESS] Morning News pipeline finished successfully!")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Personal Morning News Platform")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline and save web artifacts without sending email")
    parser.add_argument("--no-email", action="store_true", help="Skip sending email")
    parser.add_argument("--test-sources", action="store_true", help="Test news sources connectivity only")
    args = parser.parse_args()

    sys.exit(run_pipeline(dry_run=args.dry_run, no_email=args.no_email, test_sources=args.test_sources))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: implement CLI main entry and pipeline runner"
```

---

### Task 7: GitHub Actions 定时自动化与部署工作流 (`.github/workflows/` & `README.md`)

**Files:**
- Create: `.github/workflows/morning_news.yml`
- Create: `README.md`
- Test: `pytest` (全套回归验证)

**Interfaces:**
- Produces:
  - GitHub Actions cron workflow on `04:30 UTC` daily
  - Automated deployment of `public/` directory to `gh-pages` branch

- [ ] **Step 1: 创建 GitHub Actions 工作流文件**

```yaml
# .github/workflows/morning_news.yml
name: Daily Morning News Pipeline

on:
  schedule:
    # 每天 UTC 04:30 (即芬兰时间 06:30 冬令时 / 07:30 夏令时)
    - cron: '30 4 * * *'
  workflow_dispatch: # 支持网页手动点击运行

permissions:
  contents: write

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Morning News Pipeline
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_BASE_URL: ${{ secrets.LLM_BASE_URL || 'https://api.deepseek.com' }}
          LLM_MODEL: ${{ secrets.LLM_MODEL || 'deepseek-chat' }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT || '465' }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
          RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}
          SITE_URL: ${{ secrets.SITE_URL }}
        run: |
          python src/main.py

      - name: Deploy to GitHub Pages (gh-pages)
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
          keep_files: true
```

- [ ] **Step 2: 创建项目说明文档 `README.md`**

```markdown
# 个人早报自动化平台 (Morning News Platform)

每日自动抓取欧美主流财经、国际要闻与芬兰北欧新闻，经 LLM 智能提炼为结构化晨报，并通过邮件 Newsletter 与 GitHub Pages 静态网站双模发布。

## 核心特性
- **国际顶级媒体源**：FT、WSJ、CNBC、MarketWatch、SCMP、日经亚洲、路透社、BBC、Yle News、Helsinki Times。
- **AI 智能提炼**：支持 DeepSeek、Gemini、OpenAI 等任意兼容接口，多源交叉去重、提炼深度看点。
- **邮件推送**：Morning Brew 风格排版，全 CSS 内联兼容所有主流客户端。
- **Web 仪表盘**：自适应暗黑模式，由 GitHub Pages 免费托管，支持历史归档。
- **0 运维成本**：完全基于 GitHub Actions 自动化运转。

## 本地快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 复制配置并填入 API Key 与邮箱
cp .env.example .env

# 3. 快速测试新闻源连通性
python src/main.py --test-sources

# 4. 本地模拟生成晨报 (不发真实邮件，可在 public/index.html 预览)
python src/main.py --dry-run
```

## GitHub Actions 密钥配置 (Repository Secrets)
在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 中添加：
- `LLM_API_KEY`
- `LLM_BASE_URL` (例如 `https://api.deepseek.com`)
- `LLM_MODEL` (例如 `deepseek-chat`)
- `SMTP_HOST` (例如 `smtp.gmail.com`)
- `SMTP_PORT` (`465`)
- `SMTP_USER`
- `SMTP_PASS`
- `RECEIVER_EMAIL`
- `SITE_URL` (例如 `https://<username>.github.io/<repo-name>`)
```

- [ ] **Step 3: 运行全套测试验证**

Run: `pytest -v`
Expected: 全部测试通过 (100% pass)

- [ ] **Step 4: 提交代码**

```bash
git add .github/workflows/morning_news.yml README.md
git commit -m "feat: add GitHub Actions workflow and user documentation"
```
