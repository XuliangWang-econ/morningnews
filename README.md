# 个人早报自动化平台 (Morning News Platform)

每日自动抓取欧美主流财经、国际焦点大事与芬兰北欧新闻，经 LLM 智能提炼为结构化晨报，并通过邮件 Newsletter 与 GitHub Pages 静态网站双模发布。

## 🌟 核心特性
- **国际权威媒体源（无缝均衡采样）**：
  - 欧美财经：Wall Street Journal (WSJ)、Financial Times (FT)、Bloomberg Markets、MarketWatch、CNBC Finance & Business
  - 国际要闻：South China Morning Post (SCMP)、Nikkei Asia、BBC News World、France 24 International
  - 芬兰北欧：Yle News (芬兰国家广播公司)、Helsinki Times（严格排除中国大陆境内媒体）
- **信源轮询抽样与多源交叉提炼**：采用轮询平衡采样算法，彻底打破单信源垄断；Prompt 深度约束多源交叉验证与同类事件合并。
- **高韧性自动化与幂等状态机**：
  - 双重错峰调度：UTC 05:37 (芬兰冬令时 07:37) 主触发 + UTC 06:17 (芬兰冬令时 08:17) 容灾补刀触发，精准避开美东午夜批处理与欧洲上班高峰。
  - 幂等防重发：发信成功确认后才持久化 `email_sent: true` 状态；备用 cron 自动识别并跳过，防止重复轰炸收件箱。
  - 单并发控制：`concurrency: group: morning-news` 防止多实例重叠执行。
  - 时区高保真：采用 `calendar.timegm` 解析 UTC struct_time，配合内置芬兰冬夏令时回退引擎，无视操作系统差异。
- **双模体验**：
  - **邮件推送**：Morning Brew 风格排版，全 CSS 内联化，包含 `multipart/alternative`（HTML + text/plain 纯文本降级）、Message-ID 与标准日期头。
  - **Web 仪表盘**：自适应暗黑模式，由 GitHub Pages 托管，内置往期历史归档选择器与板块锚点速读导航条。
- **0 成本与 0 运维**：完全基于 GitHub Actions 自动化运转，兼容 SiliconFlow / DeepSeek 等低成本高智能模型。

---

## 🚀 本地快速开始

```bash
# 1. 创建并激活虚拟环境 (推荐)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS / Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制环境变量并填入你的 Key
cp .env.example .env

# 4. 测试各新闻源连通性
python src/main.py --test-sources

# 5. 本地模拟生成晨报 (生成 public/index.html 但不发送真实邮件)
python src/main.py --dry-run
```

---

## ⚙️ GitHub Actions 自动化部署配置

将项目推送到你的 GitHub 仓库后，在仓库中配置 Secrets：

进入 GitHub 仓库：**Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**：

| Secret 变量名 | 说明 | 示例 |
| :--- | :--- | :--- |
| `LLM_API_KEY` | 你的大模型 API Key（必填） | `sk-xxxxxx` |
| `LLM_BASE_URL` | 大模型 API 接口地址（可选，如 SiliconFlow） | `https://api.siliconflow.com/v1` |
| `LLM_MODEL` | 使用的模型标识（如 DeepSeek-V4.1-Flash） | `deepseek-ai/DeepSeek-V4.1-Flash-1017` |
| `SMTP_HOST` | 邮件发信服务器地址（必填） | `smtp.gmail.com` |
| `SMTP_PORT` | 发信端口（默认 465） | `465` (SSL) 或 `587` (TLS) |
| `SMTP_USER` | 发信邮箱账号 | `yourname@gmail.com` |
| `SMTP_PASS` | 发信邮箱授权码/应用密码 | Google 账号生成的 App Password |
| `RECEIVER_EMAIL` | 接收晨报的个人邮箱 | `yourname@gmail.com` |
| `SITE_URL` | GitHub Pages 网址 | `https://XuliangWang-econ.github.io/morningnews` |

### 开启 GitHub Pages：
在仓库的 **Settings** -> **Pages** -> **Build and deployment** -> **Source** 中选择 `Deploy from a branch`，分支选择 `gh-pages`，路径选择 `/(root)` 即可。

### 定时发信时间说明：
- 主触发：UTC 05:37（芬兰冬令时 07:37，夏令时 08:37）
- 备用触发：UTC 06:17（芬兰冬令时 08:17，夏令时 09:17）
- 手动运行：在 GitHub Actions 界面点击 **Run workflow**，支持勾选 `force` 选项强制重发。

---

## 🧪 单元测试

```bash
pytest -v
```
