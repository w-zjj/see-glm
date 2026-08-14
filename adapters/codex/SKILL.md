---
name: see-glm
description: Views and analyzes images via the GLM-4.6V vision model.
license: MIT
---

# see-glm - GLM Vision Bridge

让不支持多模态的模型通过 GLM-4.6V-Flash 查看和分析图片。
仅使用 Python 3 标准库，跨平台运行，无第三方依赖。

## 触发条件

当用户要求查看、识别、分析或描述图片，提取截图文字，比较图片差异，解读图表、流程图、架构图，或消息中出现图片文件路径时使用此 Skill。

## 使用方式

脚本路径相对于本 Skill 根目录，即 `SKILL.md` 所在目录。

调用脚本前先根据当前环境选择 Python 命令：
- 优先检查并使用 `python`
- 如果 `python` 不可用，再检查并使用 `python3`
- 不要默认假设当前环境一定提供 `python3`

在 Windows、PowerShell 和多数 Windows Agent 环境中通常使用 `python`；在部分 macOS/Linux 环境中可能需要使用 `python3`。下面示例使用 `python`，如果检查结果只有 `python3` 可用，将示例中的命令替换为 `python3`。

```bash
python scripts/see.py /path/to/image.png
python scripts/see.py /path/to/image.png --task "What's wrong in this image?"
python scripts/see.py a.png b.png c.png --jobs 3
python scripts/see.py --together before.png after.png --task "Compare the differences"
python scripts/see.py /path/to/image.png -o ./see-glm-result.md
```

## 参数

| 参数 | 说明 |
|------|------|
| `image-path/URL` | 必填，本地图片或 HTTPS URL |
| `--task "question"` | 可选，自定义问题 |
| `--together` | 可选，多图联合分析 |
| `--jobs N` | 可选，并行并发数，范围 `1-64`，默认 `3` |
| `--allow-partial` | 可选，多图部分失败时仍返回成功退出码 |
| `--model NAME` | 可选，临时覆盖模型，默认 `glm-4.6v-flash` |
| `-o FILE` | 可选，指定 Markdown 输出路径 |
| `--onboard` | 可选，启动交互式配置 |

API 临时错误会自动重试，默认最多重试 3 次，并使用指数退避及服务端返回的 `Retry-After`。
多图并行模式会保留成功结果；任一图片失败时默认返回退出码 `2`，使用 `--allow-partial` 可显式允许部分成功。

## 输出格式

成功时 stdout 只输出：

```text
output_path=/absolute/path/result.md
```

结果 Markdown 包含实际使用的模型、分析模式和模型回复。调用后读取 `output_path` 文件并将分析结果带回当前对话。

## 配置

首次使用前配置 API Key：

```bash
python scripts/onboard.py
python scripts/onboard.py --status
```

配置文件：

- Windows：`%APPDATA%\see-glm\config.env`
- macOS / Linux：`~/.config/see-glm/config.env`

支持的配置项：

```text
GLM_API_KEY=your-api-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4.6v-flash
GLM_MAX_TOKENS=8192
GLM_MAX_RETRIES=3
GLM_THINKING=disabled
```

环境变量优先于项目和用户配置。API Key 不会写入仓库。

## 安全与限制

- 支持 PNG、JPG、JPEG、GIF、WebP、BMP
- 图片以原始 Base64 发送，不会自动压缩或缩放
- 远程图片仅允许 HTTPS，并校验 DNS 解析结果和重定向目标
- 单张本地图片默认不超过 10MB，API 请求体默认不超过 20MB
- 不要上传包含密码、Token、个人身份信息或其他敏感内容的图片

## 安装

Codex 安装路径（按以下顺序扫描）：
- 仓库级：`$REPO_ROOT/.agents/skills/see-glm/`
- 用户级：`~/.agents/skills/see-glm/`
- 管理员级：`/etc/codex/skills/see-glm/`
