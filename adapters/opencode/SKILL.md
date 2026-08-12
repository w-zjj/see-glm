---
name: see-glm
description: Views and analyzes images via the GLM-4.1V vision model, bridging vision capability to non-multimodal models. Use when the user asks to view/identify/analyze/describe images (查看/识别/分析/描述图片), extract text from screenshots (截图文字提取), compare images, interpret charts/diagrams, or when image file paths (.png/.jpg/.jpeg/.gif/.webp/.bmp) appear in context.
license: MIT
compatibility: opencode
metadata:
  version: 1.0.0
  author: w-zjj
---

# see-glm — GLM Vision Bridge

Lets non-multimodal models view and analyze images via GLM-4.1V-Thinking-Flash.
Zero third-party dependencies, Python 3 standard library only, cross-platform.

## When to Use

Use this skill when the user:
- Asks to view, identify, analyze, or describe one or more images (查看/识别/分析/描述图片)
- Wants to extract text or error messages from screenshots (截图/报错图文字提取)
- Asks to compare differences between two or more images (图片对比)
- Wants to interpret charts, flowcharts, architecture diagrams, or other visual content
- Mentions image file paths (.png / .jpg / .jpeg / .gif / .webp / .bmp) in their message

Do NOT use it if the image content is already visible in the conversation (multimodal context).

## Usage

Script paths are relative to this skill's root directory (where SKILL.md lives).
On Windows, use `python` instead of `python3` if needed; forward slashes are supported.

```bash
# Single image analysis
python3 scripts/see.py /path/to/image.png

# With a custom question
python3 scripts/see.py /path/to/image.png --task "What's wrong in this image?"

# Multiple images in parallel
python3 scripts/see.py a.png b.png c.png

# Joint multi-image understanding (single request, for comparing)
python3 scripts/see.py --together a.png b.png --task "Compare the differences"

# Specify output file
python3 scripts/see.py /path/to/image.png -o /path/to/result.md

# Output to the current working directory (recommended when running under OpenCode)
python3 scripts/see.py /path/to/image.png -o ./see-glm-result.md
```

When running under OpenCode, always pass `-o` with a **relative path** so the
result Markdown lands inside the working directory. The default output location
is the system temp directory, and reading it back may require extra permission
approval (external_directory) — a relative `-o` avoids that entirely.

## Parameters

| Parameter | Purpose |
|-----------|---------|
| `image-path/URL` | Required, local file or HTTPS URL |
| `--task "question"` | Optional, custom question sent verbatim to the vision model |
| `--together` | Optional, joint multi-image mode (all images in one request) |
| `--jobs N` | Optional, parallel concurrency (default 3) |
| `--model NAME` | Optional, override model (default GLM-4.1V-Thinking-Flash) |
| `-o FILE` | Optional, output file path |
| `--onboard` | Optional, launch interactive config |

## Output Format

On success, stdout prints a single line:

```
output_path=/absolute/path/result.md
```

The result Markdown contains: model used, analysis mode, and the full vision model reply.
After calling the script, read the output_path file and bring the analysis back into the conversation.

## Installation & Configuration

OpenCode install paths:
- **Global**: `~/.config/opencode/skills/see-glm/` (all projects)
- **Project**: `<project-root>/.opencode/skills/see-glm/` (current project only)

OpenCode also auto-discovers this skill from `~/.claude/skills/see-glm/` (Claude-compatible path).

Configure API Key before first use:

```bash
python3 scripts/onboard.py
```

Check config status:

```bash
python3 scripts/onboard.py --status
```

## Config File Location

- **Windows**: `%APPDATA%\see-glm\config.env`
- **macOS / Linux**: `~/.config/see-glm/config.env`

API Key is never written to the project repo; the `GLM_API_KEY` environment variable also works.

## Notes

- Supports PNG / JPG / JPEG / GIF / WebP / BMP
- Images are sent as base64 originals (no compression or resizing) — do not analyze sensitive images
- If no API Key is configured, the script prompts to run onboard first
- Do not drag-and-drop or paste image attachments directly; save the image locally first and pass the file path
- Windows paths can use forward slashes (`C:/Users/...`)
- Zero third-party dependencies, Python 3 standard library only
