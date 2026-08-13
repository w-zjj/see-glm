#!/usr/bin/env bash
# see-glm 兼容包装 (macOS / Linux / Windows Git Bash)
# 优先使用 python，不存在时退回 python3（macOS / Linux 常见情况）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "错误: 未找到 Python，请安装 Python 3 并确保 python 命令可用。" >&2
    exit 127
fi

exec "$PY" "${SCRIPT_DIR}/see.py" "$@"
