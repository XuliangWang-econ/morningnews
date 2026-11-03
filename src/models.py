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
