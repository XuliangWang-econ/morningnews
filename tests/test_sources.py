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
