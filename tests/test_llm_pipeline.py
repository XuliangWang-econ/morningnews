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
