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
2. 时效性第一：请严格聚焦于过去24小时内的最新即时动态与今日看点，优先提炼最新发生的重大事件，忽略任何陈旧信息。
3. 专业术语精准：采用标准的财经与国际关系中文规范词汇（如 美联储利率决议、美债收益率、欧洲央行、赫尔辛基证券交易所等）。
4. 结构清晰：分为 欧美财经与全球市场、国际焦点大事、芬兰与北欧观察、一句话快讯 4 个部分。
5. 必须输出严格合法的 JSON 对象，不包含任何 Markdown 代码块标签（如 ```json ... ```），直接返回纯 JSON 字符串。
"""

def build_llm_prompt(articles_by_cat: Dict[str, List[RawArticle]], target_date_str: str) -> str:
    lines = [f"【今日晨报日期】: {target_date_str}\n", "以下是搜集到的最新原始新闻素材（全部经过24小时时效性过滤）：\n"]
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
