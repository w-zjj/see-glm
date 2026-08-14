# see-glm

![release](https://img.shields.io/github/v/release/w-zjj/see-glm?label=Latest&logo=github) ![license](https://img.shields.io/github/license/w-zjj/see-glm?logo=github) ![python](https://img.shields.io/badge/python-3.6%2B-blue?logo=python)

> **最新版本：[v1.3.1](https://github.com/w-zjj/see-glm/releases/latest)** · 以 [Releases](https://github.com/w-zjj/see-glm/releases) 中的 tag 为准，`main` 分支可能滞后于最新 release。

English: [README_EN.md](./README_EN.md)

让不支持视觉输入的 AI 编码助手通过智谱 GLM-4.6V-Flash 查看图片、读取截图文字、比较界面差异，并将结果写入 Markdown 文件。

see-glm 仅使用 Python 标准库，无需安装第三方运行时依赖，支持 Windows、macOS 和 Linux。项目同时提供 zcode、Trae、Claude Code、Codex、DeepSeek Harness、WorkBuddy 和 OpenCode 的 Skill 适配包。

## 能力

- 分析 PNG、JPG、JPEG、GIF、WebP 和 BMP 图片
- 读取本地图片或远程 HTTPS 图片
- 支持单图分析、多图并行分析和多图联合分析
- 支持自定义问题、模型、API 地址和输出路径
- 校验本地文件的真实图片格式，而不是只检查扩展名
- 校验远程地址、DNS 解析结果、重定向目标和下载内容
- 对临时网络错误和部分 API 错误自动重试
- 多图并行时保留成功结果，并明确标记失败项

## 环境要求

- Python 3.6 或更高版本
- 智谱 API Key，或兼容 OpenAI 请求格式的视觉模型接口

本文命令统一使用 `python`。如果系统只提供 `python3`，请将命令中的 `python` 替换为 `python3`。

## 快速开始

从源码运行：

```bash
git clone https://github.com/w-zjj/see-glm.git
cd see-glm
python scripts/onboard.py
python scripts/see.py screenshot.png
```

也可以从 [Releases](https://github.com/w-zjj/see-glm/releases) 下载对应工具的 ZIP 包。

成功后，标准输出只包含结果文件路径：

```text
output_path=/absolute/path/see-glm-result.md
```

打开该 Markdown 文件即可查看模型分析结果。

## 安装为 Skill

不同平台使用相同的 `scripts/`，差异只在 `SKILL.md` 元数据和安装目录。下载目标平台对应的 ZIP，将内容完整解压到下表目录：

| 平台 | ZIP 文件 | 推荐安装目录 |
|---|---|---|
| zcode | `see-glm-zcode.zip` | `~/.zcode/skills/see-glm/` |
| Trae | `see-glm-trae.zip` | `~/.trae-cn/skills/see-glm/` |
| Claude Code | `see-glm-claude.zip` | `~/.claude/skills/see-glm/` |
| Codex | `see-glm-codex.zip` | `~/.agents/skills/see-glm/` |
| DeepSeek Harness CLI | `see-glm-deepseek-harness.zip` | `~/.dsh/skills/see-glm/` |
| Dshdesk | `see-glm-deepseek-harness.zip` | `%APPDATA%\DeepSeekHarness\dsh-home\skills\see-glm\` |
| WorkBuddy | `see-glm-workbuddy.zip` | `~/.workbuddy/skills/see-glm/` |
| OpenCode | `see-glm-opencode.zip` | `~/.config/opencode/skills/see-glm/` |

解压后的目录必须直接包含以下文件，不能多套一层同名目录：

```text
see-glm/
├── SKILL.md
├── LICENSE
└── scripts/
    ├── see.py
    ├── onboard.py
    └── parse_media.py
```

安装后重新启动对应的编码助手，使其重新扫描 Skill。

### DeepSeek Harness 与 Dshdesk

[Dshdesk](https://github.com/w-zjj/dshdesk) 是 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) Web UI 的桌面封装，两者使用同一个 `see-glm-deepseek-harness.zip`，不需要单独维护 Dshdesk 适配。

两者的区别是 Skill 根目录：

- 官方 DeepSeek Harness CLI 默认使用 `~/.dsh/skills/see-glm/`
- 项目级安装可使用 `<project-root>/.dsh/skills/see-glm/`
- DeepSeek Harness 也可以发现 `.agents/skills/see-glm/`
- Dshdesk 将 `DSH_HOME` 设置为 `%APPDATA%\DeepSeekHarness\dsh-home`，因此桌面端应安装到该目录下的 `skills\see-glm`

在 Windows PowerShell 中安装 Dshdesk 版本：

```powershell
$dest = Join-Path $env:APPDATA "DeepSeekHarness\dsh-home\skills\see-glm"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Expand-Archive -Path ".\see-glm-deepseek-harness.zip" -DestinationPath $dest -Force
```

Dshdesk 内置运行 Harness 所需的 Node.js，但 see-glm 本身仍需要系统提供 `python` 或 `python3`。

## 配置 API

交互式配置：

```bash
python scripts/onboard.py
```

也可以通过主脚本启动配置：

```bash
python scripts/see.py --onboard
```

查看当前配置状态：

```bash
python scripts/onboard.py --status
```

默认配置文件：

| 平台 | 路径 |
|---|---|
| Windows | `%APPDATA%\see-glm\config.env` |
| macOS / Linux | `~/.config/see-glm/config.env` |

配置优先级从高到低为：

1. 环境变量
2. 项目根目录 `.env.local`
3. 用户配置文件

支持的配置项：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `GLM_API_KEY` | 无 | 智谱 API Key 或兼容接口 Token |
| `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | API 基础地址 |
| `GLM_MODEL` | `glm-4.6v-flash` | 视觉模型名称 |
| `GLM_MAX_TOKENS` | `8192` | 模型回复最大 Token 数 |
| `GLM_MAX_RETRIES` | `3` | 临时错误最大重试次数，限制为 `0-10` |
| `GLM_THINKING` | `disabled` | 思考模式，可选 `enabled` 或 `disabled` |

配置文件示例：

```text
GLM_API_KEY=your-api-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4.6v-flash
GLM_MAX_TOKENS=8192
GLM_MAX_RETRIES=3
GLM_THINKING=disabled
```

也可以临时设置环境变量。

Windows PowerShell：

```powershell
$env:GLM_API_KEY = "your-api-key"
```

macOS / Linux：

```bash
export GLM_API_KEY="your-api-key"
```

不要将 API Key 写入代码、提交到仓库或输出到日志。

## 使用示例

分析单张图片：

```bash
python scripts/see.py screenshot.png
```

指定分析任务：

```bash
python scripts/see.py error.png \
  --task "完整提取图片中的报错信息，并说明可能原因"
```

并行分析多张图片：

```bash
python scripts/see.py page-1.png page-2.png page-3.png --jobs 3
```

联合比较多张图片：

```bash
python scripts/see.py --together before.png after.png \
  --task "比较两个界面的布局和内容差异"
```

分析远程图片：

```bash
python scripts/see.py https://example.com/photo.jpg
```

指定输出文件：

```bash
python scripts/see.py screenshot.png --output result.md
```

## 命令参数

| 参数 | 说明 |
|---|---|
| `image-path/URL` | 一个或多个本地图片路径或 HTTPS URL |
| `--task`, `-t` | 自定义发送给视觉模型的问题 |
| `--together` | 将多张图片放入同一次 API 请求进行联合分析 |
| `--jobs`, `-j` | 并行分析的并发数，范围 `1-64`，默认 `3` |
| `--allow-partial` | 多图部分失败时仍返回退出码 `0` |
| `--model`, `-m` | 临时覆盖模型名称 |
| `--output`, `-o` | 指定 Markdown 输出路径 |
| `--onboard` | 启动交互式配置 |

多图并行模式会按照输入顺序写入结果。出现部分失败时，成功结果仍会保留，失败项会写入 `[分析失败]` 和错误原因；默认退出码为 `2`，使用 `--allow-partial` 后退出码为 `0`。

## 重试与兼容接口

网络临时错误以及以下 HTTP 状态码会触发重试：

```text
408, 429, 500, 502, 503, 504
```

等待时间优先采用服务端返回的 `Retry-After`，否则使用指数退避，单次等待最多 30 秒。认证错误、参数错误等非临时错误不会重试。

使用兼容 OpenAI 请求格式的视觉模型接口时，覆盖以下配置：

```bash
export GLM_BASE_URL="https://your-endpoint/v4"
export GLM_MODEL="your-vision-model"
export GLM_API_KEY="your-token"
```

不包含点号的 API Key 会直接作为 Bearer Token 使用；智谱标准的点号分隔 Key 会按 JWT 规则生成请求 Token。

## 安全与限制

- 单张本地图片默认不超过 10MB
- API 请求体默认不超过 20MB
- 远程图片下载大小默认不超过 50MB
- 远程图片仅允许使用 HTTPS
- 远程地址会校验 DNS 解析结果，拒绝回环、私有、链路本地和其他受限地址
- 每个重定向目标都会重新校验，最多允许 3 次重定向
- 图片以原始 Base64 发送，不会自动压缩或缩放
- 不要上传包含密码、Token、个人身份信息或其他敏感内容的图片

## 开发

运行测试：

```bash
python -m pytest -q
```

运行 Python 编译检查：

```bash
python -m compileall -q scripts tests
```

适配器由 `adapters/SKILL.template.md` 和 `adapters/metadata.json` 统一生成：

```bash
python scripts/generate_adapters.py
python scripts/generate_adapters.py --check
```

在 Windows PowerShell 中构建全部适配包：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-packages.ps1
```

生成的 ZIP 位于 `dist/`：

```text
see-glm-zcode.zip
see-glm-trae.zip
see-glm-claude.zip
see-glm-codex.zip
see-glm-deepseek-harness.zip
see-glm-workbuddy.zip
see-glm-opencode.zip
```

每个 ZIP 都包含对应平台的 `SKILL.md`、公共 `scripts/` 和 `LICENSE`。Codex 与 zcode 包额外包含 `agents/openai.yaml`。

## 项目结构

```text
see-glm/
├── scripts/
│   ├── see.py
│   ├── onboard.py
│   ├── parse_media.py
│   └── generate_adapters.py
├── adapters/
│   ├── SKILL.template.md
│   ├── metadata.json
│   ├── zcode/SKILL.md
│   ├── trae/SKILL.md
│   ├── claude/SKILL.md
│   ├── codex/SKILL.md
│   ├── deepseek-harness/SKILL.md
│   ├── workbuddy/SKILL.md
│   └── opencode/SKILL.md
├── agents/openai.yaml
├── tests/
├── build-packages.ps1
├── LICENSE
└── README.md
```

## License

[MIT](./LICENSE)
