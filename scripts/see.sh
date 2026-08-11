#!/usr/bin/env bash
# see-glm 兼容包装 (macOS / Linux / Windows Git Bash)
# 优先使用 python3，不存在时退回 python（Windows 常见情况）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

exec "$PY" "${SCRIPT_DIR}/see.py" "$@"
