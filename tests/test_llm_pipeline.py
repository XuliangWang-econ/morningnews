import json
from unittest.mock import MagicMock
from src.models import RawArticle, MorningDigest
from src.llm_pipeline import (
    build_llm_prompt,
    parse_llm_response,
    generate_morning_digest,
    sample_articles_round_robin
)

def test_sample_articles_round_robin():
    articles = []
    # 5 articles from Source A, 5 from Source B, 5 from Source C
    for i in range(5):
        articles.append(RawArticle(title=f"A{i}", summary="", url=f"http://a/{i}", source_name="SourceA"))
    for i in range(5):
        articles.append(RawArticle(title=f"B{i}", summary="", url=f"http://b/{i}", source_name="SourceB"))
    for i in range(5):
        articles.append(RawArticle(title=f"C{i}", summary="", url=f"http://c/{i}", source_name="SourceC"))

    # Sample max 6 articles total, max 2 per source
    sampled = sample_articles_round_robin(articles, max_total=6, max_per_source=2)
    assert len(sampled) == 6
    sources = [a.source_name for a in sampled]
    # First 3 should be A0, B0, C0, then A1, B1, C1
    assert sources == ["SourceA", "SourceB", "SourceC", "SourceA", "SourceB", "SourceC"]

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
    
    # 验证传入 target_date_str 会强制覆盖 LLM 潜在的幻觉日期
    digest = generate_morning_digest({}, "2026年11月05日 星期四", client=mock_client)
    assert digest.date_str == "2026年11月05日 星期四"
    assert digest.headline_quote == "早安要闻"
