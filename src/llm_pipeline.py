import os
import json
import re
import time
from typing import Dict, List, Optional
from openai import OpenAI
from src.models import RawArticle, MorningDigest

SYSTEM_PROMPT = """你是一位顶尖的国际宏观经济、全球要闻与北欧商业晨报总编。
你的任务是将提供的最新一手英文和国际新闻素材，精炼整理成一份高质量、高信息密度的中文早间晨报。

核心编辑原则：
1. 真实客观与信源平衡：严格基于提供的素材提炼，严禁捏造。每个板块必须均衡采纳不同权威媒体的报道，避免单一信源独占（财经板块均衡覆盖彭博、WSJ、FT、MarketWatch、CNBC；国际板块均衡覆盖 SCMP、Nikkei、BBC、France 24；北欧板块覆盖 Yle、Helsinki Times）。
2. 事件合并：若多家媒体同时报道了同一个重大核心事件，请合并为一条深度综合报道，并注明关键媒体与原文链接。
3. 时效性第一：严格聚焦过去24小时内的最新即时动态与今日看点，优先提炼最新发生的重大事件。
4. 数量与质量约束：
   - macro_markets（欧美财经与全球市场）：精选 3-5 条核心事件
   - global_affairs（国际焦点大事）：精选 3-5 条核心事件
   - finland_nordic（芬兰与北欧观察）：精选 2-4 条核心事件
   - quick_bites（一句话快讯）：精炼 3-5 条短讯
5. 专业术语精准：采用标准的财经与国际关系中文规范词汇（如 美联储利率决议、美债收益率、欧洲央行、赫尔辛基证券交易所等）。
6. 输出格式：必须输出严格合法的 JSON 对象，不包含任何 Markdown 代码块标签（如 ```json ... ```），直接返回纯 JSON 字符串。
"""

def sample_articles_round_robin(articles: List[RawArticle], max_total: int = 28, max_per_source: int = 5) -> List[RawArticle]:
    """按新闻源轮询抽样，确保每个信源都能进入模型 Prompt，打破单一源截断垄断"""
    by_source: Dict[str, List[RawArticle]] = {}
    for a in articles:
        by_source.setdefault(a.source_name, []).append(a)
    
    selected: List[RawArticle] = []
    indices = {k: 0 for k in by_source}
    added_any = True
    
    while added_any and len(selected) < max_total:
        added_any = False
        for src, src_articles in by_source.items():
            idx = indices[src]
            if idx < len(src_articles) and idx < max_per_source and len(selected) < max_total:
                selected.append(src_articles[idx])
                indices[src] += 1
                added_any = True
                
    return selected

def build_llm_prompt(articles_by_cat: Dict[str, List[RawArticle]], target_date_str: str) -> str:
    lines = [
        f"【今日晨报日期】: {target_date_str}\n",
        "以下是经过多信源平衡轮询采样的最新一手新闻素材（全部在24-36小时以内）：\n"
    ]
    for cat, articles in articles_by_cat.items():
        sampled = sample_articles_round_robin(articles, max_total=28, max_per_source=5)
        lines.append(f"### 板块: {cat} (共采纳 {len(sampled)} 条素材)")
        for idx, art in enumerate(sampled, 1):
            lines.append(f"{idx}. [{art.source_name}] {art.title}")
            if art.summary:
                lines.append(f"   摘要: {art.summary}")
            lines.append(f"   链接: {art.url}")
        lines.append("")
    
    lines.append("""请基于以上素材，生成包含以下字段的 JSON 对象（注意：合并重复事件，跨信源均衡选取，每个板块3-5条）：
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
    client: Optional[OpenAI] = None,
    retries: int = 2
) -> MorningDigest:
    if client is None:
        api_key = os.getenv("LLM_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=90.0)
    else:
        model = os.getenv("LLM_MODEL", "deepseek-chat")

    prompt = build_llm_prompt(articles_by_cat, target_date_str)
    
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
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
            digest = parse_llm_response(raw_content)
            # 强制覆盖日期，避免 LLM 幻觉生成错误或过期的日期
            digest.date_str = target_date_str
            return digest
        except Exception as exc:
            last_err = exc
            print(f"[WARN] LLM API attempt {attempt}/{retries} failed: {exc}")
            if attempt < retries:
                time.sleep(2.0)
                
    raise RuntimeError(f"Failed to generate morning digest from LLM after {retries} attempts: {last_err}")
