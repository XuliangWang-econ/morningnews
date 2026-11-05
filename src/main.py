import os
import sys

# 确保项目根目录在 sys.path 中，支持 python src/main.py 直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import argparse
from datetime import datetime
import httpx
from dotenv import load_dotenv

from src.timezone_utils import get_helsinki_now
from src.sources import fetch_all_categories, load_sources_config, fetch_feed
from src.llm_pipeline import generate_morning_digest
from src.renderer import render_email_html, save_web_artifacts
from src.notifier import send_email

load_dotenv()

def get_current_date_str() -> str:
    """获取赫尔辛基时区当前规范中文日期字符串"""
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    now = get_helsinki_now()
    return f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]}"

def check_already_sent_today(date_str: str, site_url: str = "") -> bool:
    """检查今天是否已经成功发信过，避免双重 Cron 触发导致重复发信"""
    # 1. 优先检查本地生成物
    local_latest = os.path.join("public", "data", "latest.json")
    if os.path.exists(local_latest):
        try:
            with open(local_latest, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date_str") == date_str and data.get("email_sent") is True:
                    return True
        except Exception as exc:
            print(f"[WARN] Failed to read local latest.json: {exc}")

    # 2. 远程 GitHub Pages 检查
    if site_url:
        try:
            url = site_url.rstrip("/") + "/data/latest.json"
            headers = {"User-Agent": "MorningNewsBot/1.0"}
            with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("date_str") == date_str and data.get("email_sent") is True:
                        return True
        except Exception as exc:
            print(f"[INFO] Remote latest.json check skipped/failed ({exc})")

    return False

def run_pipeline(dry_run: bool = False, no_email: bool = False, test_sources: bool = False, force: bool = False) -> int:
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
    site_url = os.getenv("SITE_URL", "https://XuliangWang-econ.github.io/morningnews")

    # 防重复发信机制：如果今天已经成功生成发信过，且非强制模式，则跳过
    if not force and not dry_run and check_already_sent_today(date_str, site_url):
        print(f"[INFO] Morning news for {date_str} has already been sent today. Skipping duplicate dispatch.")
        return 0

    print(f"[INFO] Starting Morning News pipeline for {date_str}...")

    # 1. 抓取所有源
    print("[1/4] Fetching news from RSS feeds...")
    articles_by_cat = fetch_all_categories()
    total_fetched = sum(len(v) for v in articles_by_cat.values())
    print(f"      Total fetched: {total_fetched} raw articles across {len(articles_by_cat)} categories.")
    if total_fetched == 0:
        print("[ERROR] Total fetched articles is 0 across all sources! Aborting pipeline to avoid hallucinated digest.")
        return 1

    # 2. LLM 提炼
    print("[2/4] Processing through LLM pipeline...")
    digest = generate_morning_digest(articles_by_cat, target_date_str=date_str)
    print(f"      LLM Digest generated: '{digest.headline_quote}'")

    # 3. 邮件推送（先发送并确认成功，发信成功后才标记 email_sent=True）
    if dry_run or no_email:
        print("[3/4] Email sending skipped (--dry-run or --no-email flag active).")
    else:
        print("[3/4] Rendering email and dispatching via SMTP...")
        email_html = render_email_html(digest, site_url=site_url)
        subject = f"今日早报 · {digest.headline_quote} ({digest.date_str})"
        success = send_email(subject, email_html)
        if not success:
            print("[ERROR] Failed to send email via SMTP! Aborting pipeline with exit code 1.")
            return 1
        digest.email_sent = True
        print("      [SUCCESS] Email sent successfully.")

    # 4. 渲染并保存 Web 产物
    print("[4/4] Rendering Web dashboard and saving artifacts to public/...")
    save_web_artifacts(digest, output_dir="public", site_url=site_url)

    print("[SUCCESS] Morning News pipeline finished successfully!")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Personal Morning News Platform")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline and save web artifacts without sending email")
    parser.add_argument("--no-email", action="store_true", help="Skip sending email")
    parser.add_argument("--test-sources", action="store_true", help="Test news sources connectivity only")
    parser.add_argument("--force", action="store_true", help="Force run even if today's digest was already sent")
    args = parser.parse_args()

    sys.exit(run_pipeline(dry_run=args.dry_run, no_email=args.no_email, test_sources=args.test_sources, force=args.force))

if __name__ == "__main__":
    main()
