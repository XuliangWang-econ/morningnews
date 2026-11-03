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
