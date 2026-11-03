# 个人早报自动化平台 (Morning News Platform)

每日自动抓取欧美主流财经、国际焦点大事与芬兰北欧新闻，经 LLM 智能提炼为结构化晨报，并通过邮件 Newsletter 与 GitHub Pages 静态网站双模发布。

## 🌟 核心特性
- **国际权威媒体源**：Financial Times、WSJ、CNBC、MarketWatch、SCMP、Nikkei Asia、Reuters、BBC News、Yle News、Helsinki Times（排除中国大陆境内源）。
- **AI 智能提炼与跨语言整合**：标准 OpenAI 协议（默认推荐高性价比 DeepSeek-V3），支持地道财经中文翻译与多源交叉去重。
- **双模体验**：
  - **邮件推送**：Morning Brew 风格排版，全 CSS 内联化，无缝适配 Apple Mail、Outlook、Gmail 移动端。
  - **Web 仪表盘**：自适应暗黑模式，由 GitHub Pages 免费托管，支持按日期历史归档。
- **0 成本与 0 运维**：完全基于 GitHub Actions 自动化定时运转。

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

将项目推送到你的 GitHub 私有/公开仓库后，只需在仓库配置 Secrets：

进入 GitHub 仓库：**Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**：

| Secret 变量名 | 说明 | 示例 |
| :--- | :--- | :--- |
| `LLM_API_KEY` | 你的大模型 API Key（必填） | `sk-xxxxxx` |
| `LLM_BASE_URL` | 大模型 API 接口地址（可选，默认 DeepSeek） | `https://api.deepseek.com` |
| `LLM_MODEL` | 使用的模型标识（可选，默认 deepseek-chat） | `deepseek-chat` |
| `SMTP_HOST` | 邮件发信服务器地址（必填） | `smtp.gmail.com` 或 `smtp.office365.com` |
| `SMTP_PORT` | 发信端口（默认 465） | `465` (SSL) 或 `587` (TLS) |
| `SMTP_USER` | 发信邮箱账号 | `yourname@gmail.com` |
| `SMTP_PASS` | 发信邮箱授权码/应用密码 | 专用的 App Password |
| `RECEIVER_EMAIL` | 接收晨报的个人邮箱 | `yourname@gmail.com` |
| `SITE_URL` | GitHub Pages 网址 | `https://<username>.github.io/<repo-name>` |

### 开启 GitHub Pages：
在仓库的 **Settings** -> **Pages** -> **Source** 中选择 `Deploy from a branch`，分支选择 `gh-pages`，路径选择 `/(root)` 即可。
工作流将在每天芬兰时间早晨 06:30（UTC 04:30）自动运行并发信。

---

## 🧪 单元测试

```bash
pytest -v
```
