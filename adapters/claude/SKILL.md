---
name: see-glm
description: Views and analyzes images via the GLM-4.1V vision model, bridging vision capability to non-multimodal models. Use when the user asks to view/identify/analyze/describe images, extract text from screenshots, compare images, interpret charts/diagrams, or when image file paths (.png/.jpg/.jpeg/.gif/.webp/.bmp) appear in context.
license: MIT
allowed-tools: Read, Write, Bash
---

# see-glm — GLM Vision Bridge

Lets non-multimodal models view and analyze images via GLM-4.1V-Thinking-Flash.
Zero third-party dependencies, Python 3 standard library only, cross-platform.

## When to Use

Use this skill when the user:
- Asks to view, identify, analyze, or describe one or more images
- Wants to extract text or error messages from screenshots
- Asks to compare differences between two or more images
- Wants to interpret charts, flowcharts, architecture diagrams, or other visual content
- Mentions image file paths (.png / .jpg / .jpeg / .gif / .webp / .bmp) in their message

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

# Joint multi-image understanding (single request)
python3 scripts/see.py --together a.png b.png --task "Compare the differences"

# Specify output file
python3 scripts/see.py /path/to/image.png -o /path/to/result.md
```

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

Claude Code install paths:
- **Personal**: `~/.claude/skills/see-glm/` (all your projects)
- **Project**: `<project-root>/.claude/skills/see-glm/` (current project only)

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
- Images are sent as base64 originals (no compression or resizing)
- If no API Key is configured, the script prompts to run onboard first
- Do not drag-and-drop or paste image attachments directly; save the image locally first and pass the file path
- Windows paths can use forward slashes (`C:/Users/...`)
- Zero third-party dependencies, Python 3 standard library only
