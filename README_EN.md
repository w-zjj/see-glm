# see-glm

![release](https://img.shields.io/github/v/release/w-zjj/see-glm?label=Latest&logo=github) ![license](https://img.shields.io/github/license/w-zjj/see-glm?logo=github) ![python](https://img.shields.io/badge/python-3.6%2B-blue?logo=python)

> **Latest release: [v1.3.1](https://github.com/w-zjj/see-glm/releases/latest)** · Release tags are the source of truth; the `main` branch may lag behind the latest release.

中文文档：[README.md](./README.md)

see-glm lets AI coding assistants without vision input inspect images, extract text from screenshots, compare UI states, and save the result as Markdown through Zhipu GLM-4.6V-Flash.

It uses only the Python standard library, requires no third-party runtime packages, and supports Windows, macOS, and Linux. Skill packages are provided for zcode, Trae, Claude Code, Codex, DeepSeek Harness, WorkBuddy, and OpenCode.

## Capabilities

- Analyze PNG, JPG, JPEG, GIF, WebP, and BMP images
- Read local images and remote HTTPS images
- Analyze one image, process multiple images in parallel, or jointly compare images
- Customize the prompt, model, API base URL, and output path
- Validate the actual local image format instead of trusting the extension
- Validate remote URLs, DNS results, redirect targets, and downloaded content
- Retry transient network and API failures
- Preserve successful results and identify failures in parallel mode

## Requirements

- Python 3.6 or later
- A Zhipu API key, or an OpenAI-compatible vision model endpoint

Commands below use `python`. Replace it with `python3` if that is the only available command.

## Quick Start

Run from source:

```bash
git clone https://github.com/w-zjj/see-glm.git
cd see-glm
python scripts/onboard.py
python scripts/see.py screenshot.png
```

You can also download the ZIP package for your target tool from [Releases](https://github.com/w-zjj/see-glm/releases).

On success, stdout contains only the result path:

```text
output_path=/absolute/path/see-glm-result.md
```

Open that Markdown file to read the model response.

## Install as a Skill

All platform packages use the same `scripts/`. Only the `SKILL.md` metadata and installation directory differ.

| Platform | ZIP package | Recommended directory |
|---|---|---|
| zcode | `see-glm-zcode.zip` | `~/.zcode/skills/see-glm/` |
| Trae | `see-glm-trae.zip` | `~/.trae-cn/skills/see-glm/` |
| Claude Code | `see-glm-claude.zip` | `~/.claude/skills/see-glm/` |
| Codex | `see-glm-codex.zip` | `~/.agents/skills/see-glm/` |
| DeepSeek Harness CLI | `see-glm-deepseek-harness.zip` | `~/.dsh/skills/see-glm/` |
| Dshdesk | `see-glm-deepseek-harness.zip` | `%APPDATA%\DeepSeekHarness\dsh-home\skills\see-glm\` |
| WorkBuddy | `see-glm-workbuddy.zip` | `~/.workbuddy/skills/see-glm/` |
| OpenCode | `see-glm-opencode.zip` | `~/.config/opencode/skills/see-glm/` |

Extract the ZIP so the target directory directly contains these files, without an extra nested `see-glm` directory:

```text
see-glm/
├── SKILL.md
├── LICENSE
└── scripts/
    ├── see.py
    ├── onboard.py
    └── parse_media.py
```

Restart the coding assistant after installation so it rescans Skills.

### DeepSeek Harness and Dshdesk

[Dshdesk](https://github.com/w-zjj/dshdesk) packages the [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) Web UI as a desktop application. Both use `see-glm-deepseek-harness.zip`; Dshdesk does not require a separate adapter.

The only relevant difference is the Skill root:

- DeepSeek Harness CLI defaults to `~/.dsh/skills/see-glm/`
- Project-level installation uses `<project-root>/.dsh/skills/see-glm/`
- DeepSeek Harness can also discover `.agents/skills/see-glm/`
- Dshdesk sets `DSH_HOME` to `%APPDATA%\DeepSeekHarness\dsh-home`, so its Skill belongs under `skills\see-glm` in that directory

Install the Dshdesk package from Windows PowerShell:

```powershell
$dest = Join-Path $env:APPDATA "DeepSeekHarness\dsh-home\skills\see-glm"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Expand-Archive -Path ".\see-glm-deepseek-harness.zip" -DestinationPath $dest -Force
```

Dshdesk bundles the Node.js runtime required by Harness, but see-glm still requires `python` or `python3` on the system.

## API Configuration

Start interactive setup:

```bash
python scripts/onboard.py
```

You can also launch setup through the main script:

```bash
python scripts/see.py --onboard
```

Show the current configuration:

```bash
python scripts/onboard.py --status
```

Default configuration files:

| Platform | Path |
|---|---|
| Windows | `%APPDATA%\see-glm\config.env` |
| macOS / Linux | `~/.config/see-glm/config.env` |

Configuration precedence:

1. Environment variables
2. `.env.local` in the project root
3. User configuration file

Supported settings:

| Setting | Default | Description |
|---|---|---|
| `GLM_API_KEY` | None | Zhipu API key or compatible endpoint token |
| `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | API base URL |
| `GLM_MODEL` | `glm-4.6v-flash` | Vision model name |
| `GLM_MAX_TOKENS` | `8192` | Maximum response tokens |
| `GLM_MAX_RETRIES` | `3` | Maximum transient-error retries, clamped to `0-10` |
| `GLM_THINKING` | `disabled` | Thinking mode: `enabled` or `disabled` |

Example:

```text
GLM_API_KEY=your-api-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4.6v-flash
GLM_MAX_TOKENS=8192
GLM_MAX_RETRIES=3
GLM_THINKING=disabled
```

Temporary environment variable on Windows PowerShell:

```powershell
$env:GLM_API_KEY = "your-api-key"
```

On macOS or Linux:

```bash
export GLM_API_KEY="your-api-key"
```

Do not put API keys in source code, commits, or logs.

## Usage

Analyze one image:

```bash
python scripts/see.py screenshot.png
```

Provide a task:

```bash
python scripts/see.py error.png \
  --task "Extract the complete error message and explain likely causes"
```

Analyze images in parallel:

```bash
python scripts/see.py page-1.png page-2.png page-3.png --jobs 3
```

Compare images jointly:

```bash
python scripts/see.py --together before.png after.png \
  --task "Compare the layout and content differences"
```

Analyze a remote image:

```bash
python scripts/see.py https://example.com/photo.jpg
```

Choose an output path:

```bash
python scripts/see.py screenshot.png --output result.md
```

## Command Options

| Option | Description |
|---|---|
| `image-path/URL` | One or more local image paths or HTTPS URLs |
| `--task`, `-t` | Custom question sent to the vision model |
| `--together` | Send multiple images in one API request for joint analysis |
| `--jobs`, `-j` | Parallel worker count, from `1-64`, default `3` |
| `--allow-partial` | Return exit code `0` when some parallel tasks fail |
| `--model`, `-m` | Override the model name |
| `--output`, `-o` | Set the Markdown output path |
| `--onboard` | Start interactive configuration |

Parallel results are written in input order. Successful results are preserved when another image fails, and each failure is written as `[分析失败]` with its error. Partial failure returns exit code `2` by default, or `0` with `--allow-partial`.

## Retries and Compatible Endpoints

Transient network errors and these HTTP status codes trigger retries:

```text
408, 429, 500, 502, 503, 504
```

The client honors `Retry-After` when present, otherwise uses exponential backoff capped at 30 seconds per delay. Authentication and request-validation errors are not retried.

For an OpenAI-compatible vision endpoint:

```bash
export GLM_BASE_URL="https://your-endpoint/v4"
export GLM_MODEL="your-vision-model"
export GLM_API_KEY="your-token"
```

An API key without a dot is sent directly as a Bearer token. A standard dot-separated Zhipu key is converted to a JWT request token.

## Security and Limits

- Local images are limited to 10MB each by default
- API request bodies are limited to 20MB by default
- Remote downloads are limited to 50MB by default
- Remote images must use HTTPS
- DNS results are checked to reject loopback, private, link-local, and other restricted addresses
- Every redirect target is revalidated, with at most 3 redirects
- Images are sent as original Base64 data without automatic compression or resizing
- Do not upload images containing passwords, tokens, personal identity data, or other sensitive information

## Development

Run tests:

```bash
python -m pytest -q
```

Compile Python sources:

```bash
python -m compileall -q scripts tests
```

Adapters are generated from `adapters/SKILL.template.md` and `adapters/metadata.json`:

```bash
python scripts/generate_adapters.py
python scripts/generate_adapters.py --check
```

Build all adapter packages from Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-packages.ps1
```

Generated ZIP files are written to `dist/`:

```text
see-glm-zcode.zip
see-glm-trae.zip
see-glm-claude.zip
see-glm-codex.zip
see-glm-deepseek-harness.zip
see-glm-workbuddy.zip
see-glm-opencode.zip
```

Each package contains its platform-specific `SKILL.md`, the shared `scripts/`, and `LICENSE`. Codex and zcode packages also include `agents/openai.yaml`.

## Project Structure

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
