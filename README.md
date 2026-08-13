# see-glm

![release](https://img.shields.io/github/v/release/w-zjj/see-glm?label=Latest&logo=github) ![license](https://img.shields.io/github/license/w-zjj/see-glm?logo=github) ![python](https://img.shields.io/badge/python-3.6%2B-blue?logo=python)

> **最新版本：[v1.3.1](https://github.com/w-zjj/see-glm/releases/latest)** · 以 [Releases](https://github.com/w-zjj/see-glm/releases) 中的 tag 为准，`main` 分支可能滞后于最新 release。

English: [README_EN.md](./README_EN.md)

让不支持视觉输入的 AI 编码助手通过智谱 GLM-4.6V-Flash 查看和分析图片，并将结果写入 Markdown 文件。

see-glm 仅使用 Python 标准库，无需安装第三方运行时依赖，支持 Windows、macOS 和 Linux。

## 特性

- 支持 PNG、JPG、JPEG、GIF、WebP、BMP
- 支持本地图片和远程 HTTPS 图片
- 支持单图分析、多图并行分析和多图联合分析
- 支持自定义问题、模型、API 地址和输出路径
- 本地图片校验真实文件头，避免仅依赖扩展名
- 远程图片校验 HTTPS、DNS 解析结果、重定向目标和真实图片格式
- API 临时错误自动重试，并支持 `Retry-After` 和指数退避
- 并行模式保留成功结果，并明确报告失败项
- 提供 zcode、Trae、Claude Code、Codex、WorkBuddy、OpenCode 适配器

## 快速开始

### 1. 获取项目

推荐从 [Releases](https://github.com/w-zjj/see-glm/releases) 下载目标工具对应的 ZIP 包。

也可以从源码运行：

```bash
git clone https://github.com/w-zjj/see-glm.git
cd see-glm
```

要求 Python 3.6 或更高版本。命令行示例统一使用 `python`；如果系统只有 `python3` 命令，请将示例中的 `python` 替换为 `python3`。

### 2. 配置 API Key

启动交互式配置：

```bash
python scripts/onboard.py
```

也可以通过主脚本启动：

```bash
python scripts/see.py --onboard
```

查看当前配置状态：

```bash
python scripts/onboard.py --status
```

默认配置文件位置：

| 平台 | 路径 |
|---|---|
| Windows | `%APPDATA%\see-glm\config.env` |
| macOS / Linux | `~/.config/see-glm/config.env` |

临时使用环境变量：

Windows PowerShell：

```powershell
$env:GLM_API_KEY = "your-api-key"
```

macOS / Linux：

```bash
export GLM_API_KEY="your-api-key"
```

API Key 不要写入代码、提交到仓库或输出到日志。

### 3. 分析图片

单图分析：

```bash
python scripts/see.py screenshot.png
```

指定任务：

```bash
python scripts/see.py error.png \
  --task "完整提取图片中的报错信息，并说明可能原因"
```

多图并行分析：

```bash
python scripts/see.py before.png after.png --jobs 3
```

多图联合分析：

```bash
python scripts/see.py --together before.png after.png \
  --task "比较两张图片的差异"
```

分析远程图片：

```bash
python scripts/see.py https://example.com/photo.jpg
```

指定输出文件：

```bash
python scripts/see.py screenshot.png --output result.md
```

成功时标准输出只包含结果文件路径：

```text
output_path=/absolute/path/result.md
```

读取该 Markdown 文件即可获得模型分析结果。

## 命令参数

| 参数 | 说明 |
|---|---|
| `image-path/URL` | 必填，一个或多个本地图片路径或 HTTPS URL |
| `--task`, `-t` | 自定义问题 |
| `--together` | 将多张图片放入一次 API 请求中联合分析 |
| `--jobs`, `-j` | 并行模式并发数，范围 `1-64`，默认 `3` |
| `--allow-partial` | 并行模式部分失败时仍返回退出码 `0` |
| `--model`, `-m` | 临时覆盖模型名称 |
| `--output`, `-o` | 指定 Markdown 输出路径 |
| `--onboard` | 启动交互式配置流程 |

### 并行失败策略

多图并行模式会按输入顺序写入结果：

- 成功的图片写入模型回复
- 失败的图片写入 `[分析失败]` 和错误原因
- 默认仍生成 Markdown，但进程返回退出码 `2`
- 使用 `--allow-partial` 可将部分成功视为成功，返回退出码 `0`

## 配置项

配置优先级从高到低为：

1. 环境变量
2. 项目根目录 `.env.local`
3. 用户配置文件

支持的配置项：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `GLM_API_KEY` | 无 | 智谱 API Key |
| `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | API 基础地址 |
| `GLM_MODEL` | `glm-4.6v-flash` | 视觉模型名称 |
| `GLM_MAX_TOKENS` | `8192` | 模型回复最大 token 数 |
| `GLM_MAX_RETRIES` | `3` | 临时错误最大重试次数，实际限制为 `0-10` |
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

### API 重试规则

以下 HTTP 状态码会触发重试：

```text
408, 429, 500, 502, 503, 504
```

网络临时错误也会触发重试。等待时间优先使用服务端返回的 `Retry-After`；未提供或无法解析时使用指数退避，单次等待最多 30 秒。认证错误、参数错误等非临时错误不会重试。

兼容 OpenAI 风格接口时，可覆盖以下配置：

```bash
export GLM_BASE_URL="https://your-endpoint/v4"
export GLM_MODEL="your-vision-model"
export GLM_API_KEY="your-token"
```

不包含点号的 API Key 会直接作为 Bearer Token 使用；智谱标准的点号分隔 Key 会按 JWT 规则生成请求 Token。

## 安全与限制

- 单张本地图片默认不超过 10MB
- API 请求体默认不超过 20MB
- 远程图片仅允许 HTTPS
- 每次远程请求都会校验域名解析地址，拒绝回环、私有、链路本地和其他受限地址
- 重定向不会无条件跟随，每个目标都会重新校验
- 远程图片最多允许 3 次重定向，下载大小默认不超过 50MB
- 图片以原始 Base64 发送，不会自动压缩或缩放
- 不要上传包含密码、Token、个人身份信息或其他敏感内容的图片

## 开发与验证

项目不需要安装第三方运行时依赖。运行测试：

```bash
python -m pytest -q
```

运行编译检查：

```bash
python -m compileall -q scripts tests
```

适配器文档由统一模板生成。修改 `adapters/SKILL.template.md` 或 `adapters/metadata.json` 后执行：

```bash
python scripts/generate_adapters.py
python scripts/generate_adapters.py --check
```

打包前会自动执行适配器漂移检查：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-packages.ps1
```

生成的 ZIP 文件位于 `dist/`，包括：

```text
see-glm-zcode.zip
see-glm-trae.zip
see-glm-claude.zip
see-glm-codex.zip
see-glm-workbuddy.zip
see-glm-opencode.zip
```

每个 ZIP 包含对应的 `SKILL.md`、公共 `scripts/` 和 `LICENSE`。Codex 与 zcode 包额外包含 `agents/openai.yaml`。

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
│   ├── workbuddy/SKILL.md
│   └── opencode/SKILL.md
├── agents/openai.yaml
├── build-packages.ps1
├── tests/test_see.py
├── LICENSE
└── README.md
```

## License

[MIT](./LICENSE)
