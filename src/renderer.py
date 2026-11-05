import os
import glob
from typing import List
from jinja2 import Environment, FileSystemLoader
from premailer import transform
from src.models import MorningDigest
from src.timezone_utils import get_helsinki_now

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

def get_jinja_env() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

def render_email_html(digest: MorningDigest, site_url: str = "") -> str:
    env = get_jinja_env()
    tmpl = env.get_template("email.html.j2")
    raw_html = tmpl.render(digest=digest, site_url=site_url)
    return transform(raw_html)

def render_web_html(digest: MorningDigest, archive_dates: List[str], site_url: str = "") -> str:
    env = get_jinja_env()
    tmpl = env.get_template("web.html.j2")
    return tmpl.render(digest=digest, archive_dates=archive_dates, site_url=site_url)

def get_archive_dates(archive_dir: str, current_date_slug: str) -> List[str]:
    dates = set()
    if os.path.exists(archive_dir):
        for path in glob.glob(os.path.join(archive_dir, "*.html")):
            base = os.path.splitext(os.path.basename(path))[0]
            if len(base) == 10 and base.count("-") == 2:
                dates.add(base)
    dates.add(current_date_slug)
    return sorted(list(dates), reverse=True)

def save_web_artifacts(digest: MorningDigest, output_dir: str = "public", site_url: str = "") -> None:
    os.makedirs(output_dir, exist_ok=True)
    archive_dir = os.path.join(output_dir, "archive")
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    today_str = get_helsinki_now().strftime("%Y-%m-%d")
    
    # 扫描已有的归档历史列表，确保网页上有归档入口
    archive_dates = get_archive_dates(archive_dir, today_str)

    # 渲染当前主页 index.html
    index_html = render_web_html(digest, archive_dates=archive_dates, site_url=site_url)
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # 渲染当日归档页
    archive_path = os.path.join(archive_dir, f"{today_str}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    # 存最新 JSON 数据备份
    json_path = os.path.join(data_dir, "latest.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(digest.model_dump_json(indent=2))
