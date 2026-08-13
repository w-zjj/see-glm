# see-glm

让不支持视觉输入的 AI 编码助手读取图片，并把分析结果写回 Markdown 文件。

see-glm 通过智谱 GLM 视觉模型分析截图、报错图片、UI 图片和多张对比图片。项目仅使用 Python 标准库，无需安装第三方依赖，支持 Windows、macOS 和 Linux。

当前版本：`v1.2.1`

## 特性

- 支持 PNG、JPG、JPEG、GIF、WebP、BMP
- 支持本地图片和远程 HTTPS 图片
- 支持单图分析、多图并行分析、多图联合分析
- 支持自定义问题、模型、API 地址和输出文件
- 本地图片会校验真实文件头，不仅依赖扩展名
- 远程图片会校验 HTTPS、DNS 解析地址、重定向目标和真实图片格式
- 默认限制单张本地图片为 10MB，API 请求体为 20MB
- 仅使用 Python 标准库
- 提供 zcode、Trae、Claude Code、Codex、WorkBuddy、OpenCode 适配器

## 快速开始

### 1. 获取项目

推荐从 [Releases](https://github.com/w-zjj/see-glm/releases) 下载对应工具的 ZIP 包。也可以从源码运行：

```bash
git clone https://github.com/w-zjj/see-glm.git
cd see-glm
```

项目要求 Python 3.6+。Windows 如果没有 `python3`，请使用 `python`。

### 2. 配置 API Key

交互式配置：

```bash
python scripts/onboard.py
```

快捷方式：

```bash
python scripts/see.py --onboard
```

查看配置状态：

```bash
python scripts/onboard.py --status
```

配置文件默认位置：

| 系统 | 路径 |
|---|---|
| Windows | `%APPDATA%\see-glm\config.env` |
| macOS / Linux | `~/.config/see-glm/config.env` |

也可以使用环境变量：

```bash
set GLM_API_KEY=your-api-key
```

```bash
export GLM_API_KEY=your-api-key
```

不要把 API Key 写入代码、提交到仓库或粘贴到日志中。

### 3. 分析图片

```bash
# 单图分析
python scripts/see.py screenshot.png

# 提取报错信息
python scripts/see.py error.png --task "请完整提取图片中的报错信息"

# 多图并行分析
python scripts/see.py before.png after.png

# 多图联合分析
python scripts/see.py --together before.png after.png \
  --task "比较两张图片的差异"

# 分析远程图片
python scripts/see.py https://example.com/photo.jpg

# 指定输出文件
python scripts/see.py screenshot.png --output result.md
```

成功时标准输出只包含一行：

```text
output_path=/absolute/path/result.md
```

结果文件包含模型、分析模式、输入文件和模型回复。

## 命令参数

| 参数 | 说明 |
|---|---|
| `图片路径/URL` | 一个或多个本地图片路径或 HTTPS URL |
| `--task`, `-t` | 自定义问题 |
| `--together` | 将多张图片放入同一次请求进行联合分析 |
| `--jobs`, `-j` | 并行分析并发数，默认 `3` |
| `--model`, `-m` | 临时覆盖模型名称 |
| `--output`, `-o` | 指定 Markdown 输出路径 |
| `--onboard` | 启动 API Key 配置流程 |

并行模式建议使用合理的 `--jobs` 值，避免同时消耗过多 API 配额。

## 配置项

配置优先级：环境变量 > 项目级 `.env.local` > 用户配置文件。

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `GLM_API_KEY` | 无 | 智谱 API Key |
| `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | API 基础地址 |
| `GLM_MODEL` | `GLM-4.1V-Thinking-Flash` | 视觉模型名称 |
| `GLM_MAX_TOKENS` | `8192` | 模型回复最大 token 数 |

兼容 OpenAI 风格服务时，可覆盖 API 地址、模型和 Bearer Token：

```bash
export GLM_BASE_URL="https://your-endpoint/v4"
export GLM_MODEL="your-vision-model"
export GLM_API_KEY="your-token"
```

智谱点号格式 API Key 会按智谱 JWT 规则生成 Token；不含点号的 Key 会直接作为 Bearer Token 使用。

## 限制与安全行为

### 图片格式

本地图片必须满足以下条件：

1. 文件扩展名属于支持列表；
2. 文件头能够识别为 PNG、JPEG、GIF、WebP 或 BMP；
3. 真实格式与扩展名一致，JPG 和 JPEG 互相兼容。

远程图片下载后也会校验真实文件头。HTML、JSON 或无法识别的二进制内容不会继续发送给视觉 API。

### 远程 URL

远程图片仅允许 HTTPS。下载器会：

- 拒绝回环、私有、链路本地、未指定、组播和保留地址；
- 对域名的 DNS 解析结果进行校验；
- 禁止自动跟随重定向，逐跳校验重定向目标；
- 默认最多跟随 3 次重定向；
- 默认最多下载 50MB。

这套校验用于降低脚本被自动化调用时访问本机、内网或云元数据服务的 SSRF 风险。

### 大小与编码

当前版本不会对图片进行压缩或缩放，而是发送经过格式校验的原图。为避免 Base64 编码造成过大请求：

- 单张本地图片默认不超过 10MB；
- 最终 API 请求体默认不超过 20MB；
- 超出限制会在本地报错，不会发送请求。

### 隐私

图片内容会被编码后发送到配置的视觉模型服务。请勿上传包含密码、Token、个人身份信息或其他敏感内容的图片。

## Release 包

使用根目录的打包脚本生成六个工具包：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-packages.ps1
```

生成文件：

```text
dist/
├── see-glm-zcode.zip
├── see-glm-trae.zip
├── see-glm-claude.zip
├── see-glm-codex.zip
├── see-glm-workbuddy.zip
└── see-glm-opencode.zip
```

每个 ZIP 包含对应的 `SKILL.md`、公共 `scripts/` 和 `LICENSE`。Codex 与 zcode 包还包含 `agents/openai.yaml`。

## 开发与验证

运行测试：

```bash
python -m pytest -q
```

运行编译检查：

```bash
python -m compileall -q scripts tests
```

项目测试不需要真实 API Key，也不会调用真实视觉 API。

## 项目结构

```text
see-glm/
├── scripts/
│   ├── see.py
│   ├── onboard.py
│   ├── parse_media.py
│   └── see.sh
├── adapters/
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
