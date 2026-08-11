# see-glm — 让 AI 看懂图片的视觉桥接工具

为非多模态模型（如纯文本 LLM、编码助手）提供图片理解能力：通过调用 **GLM-4.1V-Thinking-Flash** 视觉模型，把图片分析结果带回当前会话。零第三方依赖，纯 Python 标准库，跨平台。

[English](#english) | 中文

## 为什么需要它？

很多 AI 编码助手 / CLI 使用的模型不支持图片输入（截图、报错图、UI 图都无法"看见"）。see-glm 提供了一条简单的桥接路径：

```
不支持视觉的模型
  │ 看到图片路径后调用
  ▼
see.py ──base64 原图──▶ GLM-4.1V API ──▶ 视觉理解结果
  ◀─────────────────────────────────┘
  结果写回 Markdown 文件，模型直接读取
```

## 特性

- 🖼️ **零依赖**：仅用 Python 3 标准库，克隆即用，无需 pip install
- 🌍 **跨平台**：Windows / macOS / Linux
- 📦 **多格式**：PNG / JPG / JPEG / GIF / WebP / BMP，支持本地文件和 HTTPS URL
- ⚡ **三种模式**：单图分析、多图并行分析（可调并发）、多图联合理解（同一上下文比较差异）
- 🔑 **安全**：API Key 保存在用户私有目录，绝不写入代码或仓库；Unix 下自动设置 600 权限
- 🔧 **可配置**：模型名、Base URL 均可覆盖，理论上可对接 OpenAI 兼容端点
- 🎯 **多工具适配**：一份脚本，支持 zcode / Trae / Claude Code / Codex / WorkBuddy 五大 AI 编码助手

## 快速开始

### 方式一：下载 Release 包（推荐）

从 [Releases](https://github.com/w-zjj/see-glm/releases) 下载对应工具的压缩包，解压到该工具的 skill 目录即可。

| 工具 | 下载文件 | 解压路径 |
|------|---------|---------|
| zcode | `see-glm-zcode.zip` | `~/.zcode/skills/see-glm/` |
| Trae | `see-glm-trae.zip` | `~/.trae-cn/skills/see-glm/`（用户级）或 `<项目>/.trae/skills/see-glm/`（项目级） |
| Claude Code | `see-glm-claude.zip` | `~/.claude/skills/see-glm/`（个人级）或 `<项目>/.claude/skills/see-glm/`（项目级） |
| Codex | `see-glm-codex.zip` | `~/.agents/skills/see-glm/`（用户级）或 `<项目>/.agents/skills/see-glm/`（项目级） |
| WorkBuddy | `see-glm-workbuddy.zip` | `~/.workbuddy/skills/see-glm/`（用户级）或 `<项目>/.workbuddy/skills/see-glm/`（项目级） |

解压后目录结构（每个包都一样）：

```
see-glm/
├── SKILL.md          # 该工具专用的 frontmatter 适配版
├── scripts/
│   ├── see.py        # 主入口
│   ├── onboard.py    # 配置 API Key
│   ├── parse_media.py
│   └── see.sh
└── LICENSE
```

### 方式二：从源码克隆

```bash
git clone https://github.com/w-zjj/see-glm.git
cd see-glm
```

仓库里 `adapters/` 目录下有 5 个工具的专用 SKILL.md，按需复制到对应 skill 目录：

```bash
# 以 zcode 为例
mkdir -p ~/.zcode/skills/see-glm
cp -r scripts ~/.zcode/skills/see-glm/
cp adapters/zcode/SKILL.md ~/.zcode/skills/see-glm/
cp LICENSE ~/.zcode/skills/see-glm/
```

### 配置 API Key

首次使用前需要配置智谱 API Key：

```bash
python3 scripts/onboard.py
# 或一键配置：python3 scripts/see.py --onboard
# 查看配置状态：python3 scripts/onboard.py --status
```

Windows 上如果 `python3` 不在 PATH，请改用 `python`。

### 分析图片

```bash
# 单图分析
python3 scripts/see.py screenshot.png

# 带自定义问题（原样发送给视觉模型）
python3 scripts/see.py error.png --task "请提取截图中的报错信息"

# 多图并行分析（默认 3 并发）
python3 scripts/see.py a.png b.png c.png

# 多图联合理解：所有图进入同一次请求，适合比较差异
python3 scripts/see.py --together before.png after.png --task "比较两张图的差异"

# 分析网络图片
python3 scripts/see.py https://example.com/photo.jpg

# 指定结果输出文件
python3 scripts/see.py image.png -o result.md

# 临时覆盖模型
python3 scripts/see.py image.png --model glm-4v-plus
```

## 参数

| 参数 | 用途 |
|---|---|
| `图片路径/URL` | 必填，支持本地文件和 HTTPS URL |
| `--task "问题"` | 可选，自定义提问，原样发送给视觉模型 |
| `--together` | 可选，多图联合理解模式 |
| `--jobs N` | 可选，并行模式并发数（默认 3） |
| `--model NAME` | 可选，临时覆盖模型 |
| `-o FILE` | 可选，指定结果输出文件路径 |
| `--onboard` | 可选，快捷启动配置流程 |

### 输出

成功后 stdout 只输出一行，方便脚本捕获：

```
output_path=/absolute/path/result.md
```

结果 Markdown 包含：使用的模型、分析模式、视觉模型的完整回复。

## 配置

优先级：**环境变量 > 项目级 `.env.local` > 用户配置文件**

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `GLM_API_KEY` | — | 智谱 API Key（`xxxx.xxxx` 格式，[open.bigmodel.cn](https://open.bigmodel.cn/) 获取） |
| `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | API 地址 |
| `GLM_MODEL` | `GLM-4.1V-Thinking-Flash` | 模型名 |
| `GLM_MAX_TOKENS` | `8192` | 单次回复最大 token 数（thinking 模型思维链较长，建议 ≥8192） |

配置文件位置（由 onboard.py 生成）：

- **Windows**: `%APPDATA%\see-glm\config.env`
- **macOS / Linux**: `~/.config/see-glm/config.env`

⚠️ **切勿将 `.env.local` 或 `config.env` 提交到版本控制**（已包含在 .gitignore 中）。

### 对接其他模型服务

代码默认使用智谱 API。想换其他兼容服务时：

```bash
export GLM_BASE_URL="https://your-endpoint/v4"
export GLM_MODEL="your-vision-model"
export GLM_API_KEY="your-key"
```

注意：智谱 API Key 的 JWT 签名是智谱特有的；`see.py` 检测到无点号分隔的 Key 时会直接作为 Bearer Token 发送，可兼容部分 OpenAI 风格端点，但不同服务的鉴权方式请以官方文档为准。

## 仓库结构

```
see-glm/
├── scripts/              # 共用脚本（所有工具一样）
│   ├── see.py            # 主入口：校验 → 编码 → 调 API → 写结果
│   ├── onboard.py        # 交互式配置 API Key
│   ├── parse_media.py    # 媒体工具：校验 / base64 / MIME / 尺寸
│   └── see.sh            # bash 包装（python3 / python 自动降级）
├── adapters/             # 各工具的 SKILL.md 适配版
│   ├── zcode/SKILL.md
│   ├── trae/SKILL.md
│   ├── claude/SKILL.md
│   ├── codex/SKILL.md
│   └── workbuddy/SKILL.md
├── agents/
│   └── openai.yaml       # Codex/zcode Agent 框架适配配置
├── build-packages.ps1    # 打包脚本（生成 5 个独立 zip）
├── README.md
├── LICENSE
└── .gitignore
```

## 各工具适配说明

五个工具都遵循 [Agent Skills 开放标准](https://agentskills.io/)，核心都是 `SKILL.md` + frontmatter。差异主要在 frontmatter 字段和扫描路径：

| 工具 | 扫描路径（用户级） | frontmatter 特殊字段 |
|------|------------------|---------------------|
| zcode | `~/.zcode/skills/` | 无特殊，配合 `agents/openai.yaml` |
| Trae | `~/.trae-cn/skills/` 或 `<项目>/.trae/skills/` | `supported_os` |
| Claude Code | `~/.claude/skills/` 或 `<项目>/.claude/skills/` | `allowed-tools` 可选 |
| Codex | `~/.agents/skills/` 或 `<项目>/.agents/skills/` | 无特殊，推荐 `agents/openai.yaml` |
| WorkBuddy | `~/.workbuddy/skills/` 或 `<项目>/.workbuddy/skills/` | `allowed-tools`、`metadata` |

## 打包发布

仓库根目录的 `build-packages.ps1` 可一键生成 5 个独立 zip 包：

```powershell
# 在仓库根目录执行
.\build-packages.ps1
```

生成的包在 `dist/` 目录下：

```
dist/
├── see-glm-zcode.zip
├── see-glm-trae.zip
├── see-glm-claude.zip
├── see-glm-codex.zip
└── see-glm-workbuddy.zip
```

每个包内含该工具专用的 `SKILL.md` + 共用 `scripts/` + `LICENSE`，解压即用。

## 注意事项

- 图片以 base64 **原图** 发送到智谱云端，不压缩不缩放；请勿分析敏感图片
- 免费/付费额度由智谱账号决定，多图并行模式会同时消耗多份额度
- 需要 Python 3.6+（仅标准库）

## License

[MIT](./LICENSE)

---

<a id="english"></a>
# see-glm — Vision Bridge for AI to See Images

Provides image understanding for non-multimodal models (e.g. text-only LLMs, coding assistants): calls the **GLM-4.1V-Thinking-Flash** vision model and brings the analysis result back to the current session. Zero third-party dependencies, pure Python standard library, cross-platform.

## Why need it?

Many AI coding assistants / CLIs use models that don't support image input (screenshots, error images, UI images — all invisible). see-glm provides a simple bridging path:

```
Non-vision model
  │ sees image path, calls script
  ▼
see.py ──base64 original──▶ GLM-4.1V API ──▶ vision result
  ◀─────────────────────────────────┘
  result written to Markdown, model reads it
```

## Features

- 🖼️ **Zero dependencies**: Python 3 standard library only, clone and run, no pip install
- 🌍 **Cross-platform**: Windows / macOS / Linux
- 📦 **Multi-format**: PNG / JPG / JPEG / GIF / WebP / BMP, local files and HTTPS URLs
- ⚡ **Three modes**: single image, parallel multi-image (adjustable concurrency), joint multi-image (compare in one context)
- 🔑 **Secure**: API Key stored in user-private directory, never in code or repo; auto 600 perms on Unix
- 🔧 **Configurable**: model name and Base URL overridable, compatible with OpenAI-style endpoints
- 🎯 **Multi-tool adapter**: one set of scripts supports zcode / Trae / Claude Code / Codex / WorkBuddy

## Quick Start

### Option 1: Download Release (recommended)

Download the zip for your tool from [Releases](https://github.com/w-zjj/see-glm/releases) and extract to that tool's skill directory.

| Tool | Download | Extract to |
|------|----------|-----------|
| zcode | `see-glm-zcode.zip` | `~/.zcode/skills/see-glm/` |
| Trae | `see-glm-trae.zip` | `~/.trae-cn/skills/see-glm/` (user) or `<project>/.trae/skills/see-glm/` (project) |
| Claude Code | `see-glm-claude.zip` | `~/.claude/skills/see-glm/` (personal) or `<project>/.claude/skills/see-glm/` (project) |
| Codex | `see-glm-codex.zip` | `~/.agents/skills/see-glm/` (user) or `<project>/.agents/skills/see-glm/` (project) |
| WorkBuddy | `see-glm-workbuddy.zip` | `~/.workbuddy/skills/see-glm/` (user) or `<project>/.workbuddy/skills/see-glm/` (project) |

### Option 2: Clone from source

```bash
git clone https://github.com/w-zjj/see-glm.git
cd see-glm
```

The `adapters/` directory contains tool-specific SKILL.md files. Copy the one you need along with `scripts/` to your tool's skill directory.

### Configure API Key

```bash
python3 scripts/onboard.py
# or: python3 scripts/see.py --onboard
# check status: python3 scripts/onboard.py --status
```

On Windows, use `python` instead of `python3` if needed.

### Analyze images

```bash
python3 scripts/see.py screenshot.png
python3 scripts/see.py error.png --task "Extract the error message"
python3 scripts/see.py a.png b.png c.png
python3 scripts/see.py --together before.png after.png --task "Compare differences"
python3 scripts/see.py https://example.com/photo.jpg
python3 scripts/see.py image.png -o result.md
```

## License

[MIT](./LICENSE)
