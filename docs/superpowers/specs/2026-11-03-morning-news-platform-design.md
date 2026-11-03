# 个人早报自动化平台系统设计规范 (Spec)

- **创建日期**: 2026-11-03
- **项目状态**: 待执行
- **目标用户**: 个人自用
- **核心定位**: 每日早间自动生成高品质晨报，结合“国际综合要闻”、“欧美主流财经商业”与“芬兰/北欧动态”，通过优雅的 HTML 邮件每日推送，并同步更新至自托管的 Web 仪表盘。

---

## 1. 系统概述与核心目标

构建一个轻量、稳定、免运维的个人早报平台。系统具备以下核心特征：
1. **权威国际化信息源**：排除中国大陆媒体，聚焦欧美主流财经（FT、WSJ、CNBC、MarketWatch）、亚太及国际主流综合媒体（SCMP、Nikkei Asia、Reuters、BBC、联合早报）以及芬兰国家媒体（Yle News、Helsinki Times）。
2. **AI 智能提炼与跨语言整合**：利用兼容 OpenAI 协议的高性价比 LLM（如 DeepSeek-V3），执行多源去重、重要度提炼、深度摘要翻译与结构化产出。
3. **双模消费体验**：
   - **邮件推送**：每天早间准时推送至个人邮箱，版式遵循 Morning Brew / FT 风格，全内联 CSS 确保在 Apple Mail、Outlook、Gmail 移动端完美渲染。
   - **Web 仪表盘**：自适应移动端与桌面端，提供暗黑模式与历史归档浏览，托管于 GitHub Pages。
4. **零成本与零服务器运维**：由 GitHub Actions 定时触发构建流水线，代码与归档统一存储于 Git 仓库，无需租用 VPS。

---

## 2. 系统架构与模块职责

系统采用**单向流式管道（Pipeline）**架构，各模块松耦合设计：

```
+-------------------------------------------------------------+
|                     GitHub Actions (Cron)                    |
|                或 本地命令行 (python main.py)                 |
+-------------------------------------------------------------+
                              |
                              v
                  [ 1. 数据采集: sources.py ]
                              |  抓取各大 RSS，过滤 24h 内条目
                              v
                [ 2. AI 智能处理: llm_pipeline.py ]
                              |  调用 LLM 进行去重、翻译与提炼
                              v
                 [ 3. 模板渲染: renderer.py ]
                    /                     \
                   v                       v
      [ 邮件 HTML (inlined) ]      [ Web HTML (public/) ]
                   |                       |
                   v                       v
       [ 4. 推送: notifier.py ]   [ 5. 发布: gh-pages 分支 ]
                   |                       |
                   v                       v
              个人邮箱收件箱              在线静态网站
```

### 模块详细划分

| 模块文件 | 职责说明 | 关键依赖 |
| :--- | :--- | :--- |
| `config/sources.yaml` | 声明式数据源配置，支持随时扩展与分类 | `PyYAML` |
| `src/sources.py` | 负责并发拉取 RSS 源，做超时保护、时区清洗与前置去重 | `feedparser`, `httpx` |
| `src/llm_pipeline.py` | 构造 Prompt，调用 LLM，解析并用 Pydantic 校验结构化 JSON | `openai`, `pydantic` |
| `src/renderer.py` | 使用 Jinja2 将结构化 JSON 渲染为邮件 HTML 和静态 Web 页面 | `jinja2`, `premailer` |
| `src/notifier.py` | 通过标准 SMTP 发送邮件，处理发信认证与异常重试 | 原生 `smtplib`, `email` |
| `src/main.py` | CLI 入口，编排全流程，提供 `--dry-run`、`--no-email` 等调试开关 | `argparse` |

---

## 3. 信息源规划 (`config/sources.yaml`)

系统预设三大内容板块：

```yaml
# 1. 欧美主流财经与宏观市场
finance_markets:
  - name: "Financial Times (FT)"
    url: "https://www.ft.com/rss/home/us"
  - name: "Wall Street Journal (WSJ Markets)"
    url: "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
  - name: "CNBC Top News"
    url: "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date"
  - name: "MarketWatch"
    url: "https://feeds.content.dowjones.io/public/rss/mw_topstories"

# 2. 国际综合要闻
global_news:
  - name: "South China Morning Post (SCMP)"
    url: "https://www.scmp.com/rss/91/feed"
  - name: "Nikkei Asia"
    url: "https://asia.nikkei.com/rss/feed/nar"
  - name: "Reuters World"
    url: "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=best"
  - name: "BBC News World"
    url: "http://feeds.bbci.co.uk/news/world/rss.xml"
  - name: "Lianhe Zaobao (国际)"
    url: "https://www.zaobao.com.sg/rss/realtime/world"

# 3. 芬兰与北欧要闻
finland_nordic:
  - name: "Yle News (芬兰国家广播公司)"
    url: "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_NEWS"
  - name: "Helsinki Times"
    url: "https://www.helsinkitimes.fi/finland?format=feed&type=rss"
```

### 抓取策略与性能约束
- 单源超时设为 10 秒，抓取失败自动降级跳过；
- 仅保留过去 24 小时发布的内容；
- 每个分类保留最新 8~12 条高质量候选资讯传入大模型。

---

## 4. LLM 提炼规范与数据契约

### Pydantic 数据模型定义
```python
class NewsItem(BaseModel):
    title: str          # 中文提炼标题
    summary: str        # 2-3 句中文核心事件经过
    impact: str         # 深度解读 / 商业市场影响 / 后续看点
    source_name: str    # 媒体名称（如 Financial Times）
    url: str            # 原始文章跳转链接

class MorningDigest(BaseModel):
    date_str: str       # 格式：YYYY年MM月DD日 星期X
    headline_quote: str # 今日晨报宏观脉搏一句话金句
    macro_markets: list[NewsItem]     # 3-4条 欧美财经与商业要闻
    global_affairs: list[NewsItem]    # 3-4条 国际重要局势
    finland_nordic: list[NewsItem]    # 2-3条 芬兰本地与北欧观察
    quick_bites: list[str]            # 3-5条 一句话速览短快讯
```

### Prompt 设计准则
1. **客观准确**：严格基于输入内容提炼，不臆造虚构事实；
2. **金融与时政语境准确**：对欧美央行决议、金融衍生品、宏观指标等使用行业通用中文规范名词；
3. **高信息密度**：删除冗余修饰词，保留数字、因果关系与核心当事方观点。

---

## 5. 排版渲染规范

### 1. 邮件 Newsletter 模板 (`templates/email.html.j2`)
- **视觉风格**：现代报刊风格（Off-white 背景 `#f8f9fa`，深石墨色文字 `#1a1a1a`，点缀色 `#0052cc`）。
- **兼容性保障**：使用 `premailer` 进行 CSS 内联化，确保主流邮件客户端（Gmail / Outlook / Apple Mail）在手机和桌面均无样式溢出或排版变形。
- **内容层次**：
  1. Header：日期、星期、主编早安金句；
  2. 3分钟速读导航框；
  3. 板块一：欧美财经与全球市场；
  4. 板块二：国际大事与全球地缘；
  5. 板块三：芬兰与北欧本地；
  6. 板块四：扫一眼快讯（Quick Bites）；
  7. Footer：生成时间、归档网页跳转链接。

### 2. 静态 Web 仪表盘 (`templates/web.html.j2`)
- **输出目录**：`public/index.html`（今日最新）与 `public/archive/YYYY-MM-DD.html`（往期存档）。
- **交互与功能**：
  - 纯原生 HTML/CSS/JS，极速加载；
  - 支持系统偏好深色/浅色模式自适应切换；
  - 顶部/侧边简易日期切换器，支持查看往期归档；
  - 卡片式阅读排版，正文阅读区锁定 720px 宽度。

---

## 6. 环境配置与安全隔离

项目通过 `.env`（本地开发）和 GitHub Secrets（自动化运行）注入配置：

```bash
# 大模型配置 (支持 OpenAI 兼容 API，推荐 DeepSeek)
LLM_API_KEY="sk-xxxxxxxx"
LLM_BASE_URL="https://api.deepseek.com"
LLM_MODEL="deepseek-chat"

# 邮件 SMTP 配置
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=465
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-app-password"
RECEIVER_EMAIL="your-email@gmail.com"

# 站点配置
SITE_URL="https://<username>.github.io/<repo-name>"
```

---

## 7. 自动化流水线 (`.github/workflows/morning_news.yml`)

- **Cron 调度**：每天芬兰时间早晨 06:30（UTC 04:30）。
- **触发机制**：`schedule` + `workflow_dispatch`（支持在 GitHub 网页手动点击触发）。
- **执行步骤**：
  1. `actions/checkout@v4` 检出仓库代码；
  2. `actions/setup-python@v5` 配置 Python 3.11 环境；
  3. 恢复 `pip` 缓存并安装依赖；
  4. 执行 `python src/main.py`；
  5. 将 `public/` 产物自动发布至 `gh-pages` 分支。

---

## 8. 本地调试与测试保障

开发时提供完善的命令行开关：
- `python src/main.py --dry-run`：执行完整抓取、LLM 提炼与页面渲染，但不发出真实邮件，产物输出在 `public/` 下便于本地直接用浏览器打开查看。
- `python src/main.py --test-sources`：仅测试各 RSS 源的网络连通性与内容解析，打印耗时与条数。
- 提供核心处理模块的单元测试（`pytest`），覆盖 RSS 解析、LLM 响应校验与模板渲染。
