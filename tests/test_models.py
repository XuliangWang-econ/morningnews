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
