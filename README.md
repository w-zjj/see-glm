# see-glm — 让 AI 看懂图片的视觉桥接工具

> 为非多模态模型（如纯文本 LLM、编码助手）提供图片理解能力：通过调用
> **GLM-4.1V-Thinking-Flash** 视觉模型，把图片分析结果带回当前会话。
> 零第三方依赖，纯 Python 标准库，跨平台。

[English](#english) | 中文

## 为什么需要它？

很多 AI 编码助手 / CLI 使用的模型不支持图片输入（截图、报错图、UI 图都无法"看见"）。
see-glm 提供了一条简单的桥接路径：

```
不支持视觉的模型
      │  看到图片路径后调用
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

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/w-zjj/see-glm.git
cd see-glm

# 2. 配置 API Key（首次使用）
python3 scripts/onboard.py
# 或一键配置：python3 scripts/see.py --onboard

# 3. 查看配置状态
python3 scripts/onboard.py --status

# 4. 分析图片
python3 scripts/see.py /path/to/image.png --task "这张图里有什么？"
```

> Windows 上如果 `python3` 不在 PATH，请改用 `python`。

## 用法

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

### 参数

| 参数 | 用途 |
|------|------|
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
|--------|--------|------|
| `GLM_API_KEY` | — | 智谱 API Key（`xxxx.xxxx` 格式，[open.bigmodel.cn](https://open.bigmodel.cn) 获取） |
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

注意：智谱 API Key 的 JWT 签名是智谱特有的；`see.py` 检测到无点号分隔的 Key 时会直接
作为 Bearer Token 发送，可兼容部分 OpenAI 风格端点，但不同服务的鉴权方式请以官方文档为准。

## 项目结构

```
see-glm/
├── SKILL.md              # AI 助手 skill 定义（含触发条件和用法）
├── scripts/
│   ├── see.py            # 主入口：校验 → 编码 → 调 API → 写结果
│   ├── onboard.py        # 交互式配置 API Key
│   ├── parse_media.py    # 媒体工具：校验 / base64 / MIME / 尺寸
│   └── see.sh            # bash 包装（python3 / python 自动降级）
└── agents/
    └── openai.yaml       # Agent 框架适配配置（Codex / zcode 等）
```

## 作为 AI Skill 使用

本项目同时是一个 ZCode / Claude Code 等工具可发现的 skill（`SKILL.md`）。
安装到用户级 skill 目录后，AI 助手在收到图片分析请求时会自动触发。
脚本路径建议使用仓库绝对路径，例如：

```bash
python3 /path/to/see-glm/scripts/see.py /path/to/image.png
```

## 注意事项

- 图片以 base64 **原图**发送到智谱云端，不压缩不缩放；请勿分析敏感图片
- 免费/付费额度由智谱账号决定，多图并行模式会同时消耗多份额度
- 需要 Python 3.6+（仅标准库）

## License

[MIT](./LICENSE)
