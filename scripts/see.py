#!/usr/bin/env python3
"""
see-glm — 通过 GLM-4.1V-Thinking-Flash 让 AI 查看图片
跨平台主入口 (Windows / macOS / Linux)
用法:
  python3 see.py image.png
  python3 see.py image.png --task "这张图里有什么？"
  python3 see.py a.png b.png c.png
  python3 see.py --together a.png b.png --task "比较差异"
  python3 see.py image.png -o result.md
  python3 see.py image.png --model GLM-4.1V-Thinking-Flash
"""
import os
import re
import sys
import json
import time
import base64
import hashlib
import hmac
import argparse
import subprocess
import socket
import tempfile
import ipaddress
import urllib.request
import urllib.error
import urllib.parse
import concurrent.futures
from pathlib import Path
from datetime import datetime

# ---- 常量 ----
DEFAULT_MODEL = "GLM-4.1V-Thinking-Flash"
DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_JOBS = 3
SUPPORTED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
MIME_MAP = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
}
DEFAULT_MAX_TOKENS = 8192
# 下载图片的大小上限（50MB），防止意外下载超大文件
DEFAULT_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_REDIRECTS = 3
# GLM thinking 模型回复中可能出现的内置特殊 token
THINKING_TOKEN_PATTERN = re.compile(
    r"<\|(?:begin_of_box|end_of_box|thought|endofthought)\|>"
)


# ---- 跨平台配置目录 ----
def get_config_dir():
    """获取配置目录，跨平台"""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", "")
        if base:
            return Path(base) / "see-glm"
        return Path.home() / ".config" / "see-glm"
    else:
        return Path.home() / ".config" / "see-glm"


# ---- 配置加载 ----
def load_config():
    """加载配置: 环境变量 > 项目 .env.local > 用户配置文件"""
    config = {}
    # 1. 用户私有配置
    config_file = get_config_dir() / "config.env"
    if config_file.is_file():
        for line in config_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    # 2. 项目级 .env.local
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    project_env = project_root / ".env.local"
    if project_env.is_file():
        for line in project_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    # 3. 环境变量优先级最高（覆盖已有值）
    for key in ("GLM_API_KEY", "GLM_BASE_URL", "GLM_MODEL", "GLM_MAX_TOKENS"):
        env_val = os.environ.get(key, "")
        if env_val:
            config[key] = env_val
    return config


# ---- JWT 生成 ----
def generate_jwt(api_key):
    """生成智谱 API JWT Token"""
    if "." not in api_key:
        # 没有点号分隔，直接当作 Bearer token
        return api_key
    id_part = api_key.split(".")[0]
    secret_part = api_key.split(".", 1)[1]
    # Header
    header = json.dumps({"alg": "HS256", "sign_type": "SIGN"}, separators=(',', ':'))
    header_b64 = base64.urlsafe_b64encode(header.encode()).rstrip(b'=').decode()
    # Payload
    now = int(time.time())
    payload = json.dumps({
        "api_key": id_part,
        "exp": now + 3600,
        "timestamp": now
    }, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).rstrip(b'=').decode()
    # Signature
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret_part.encode(),
        signing_input.encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    return f"{header_b64}.{payload_b64}.{sig_b64}"


# ---- 文件工具 ----
def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def get_ext(filepath):
    return Path(filepath).suffix.lstrip(".").lower()


def get_mime(filepath):
    ext = get_ext(filepath)
    return MIME_MAP.get(ext, "image/png")


def validate_file(filepath):
    """校验文件，返回 (abs_path_or_url, is_url) 或抛出异常"""
    if is_url(filepath):
        return filepath, True
    p = Path(filepath)
    if not p.is_file():
        raise FileNotFoundError(f"文件不存在: {filepath}")
    ext = get_ext(filepath)
    if ext not in SUPPORTED_EXT:
        raise ValueError(f"不支持的格式 .{ext}，仅支持: {', '.join(sorted(SUPPORTED_EXT))}")
    return str(p.resolve()), False


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Return redirect responses so callers can validate every target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

    def http_error_301(self, req, fp, code, msg, headers):
        return fp

    http_error_302 = http_error_301
    http_error_303 = http_error_301
    http_error_307 = http_error_301
    http_error_308 = http_error_301


def _validate_public_https_url(url):
    """Reject non-HTTPS and targets resolving to local or reserved addresses."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"远程图片仅允许使用 HTTPS URL: {url}")
    if not parsed.hostname:
        raise ValueError(f"URL 缺少主机名: {url}")
    try:
        port = parsed.port or 443
    except ValueError as e:
        raise ValueError(f"URL 端口无效: {url}") from e

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, port, type=socket.SOCK_STREAM
        )
    except socket.gaierror as e:
        raise ValueError(f"无法解析远程图片主机名 {parsed.hostname}: {e}") from e
    if not addresses:
        raise ValueError(f"远程图片主机名未解析出地址: {parsed.hostname}")

    for address in addresses:
        ip_text = address[4][0]
        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError as e:
            raise ValueError(f"远程图片主机名解析出无效地址: {ip_text}") from e
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_unspecified
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise ValueError(
                f"远程图片地址解析到受限网络地址，已拒绝: {parsed.hostname} ({ip})"
            )


def _open_download_url(request, timeout):
    opener = urllib.request.build_opener(_NoRedirectHandler())
    return opener.open(request, timeout=timeout)


def download_url(
    url,
    max_bytes=DEFAULT_MAX_DOWNLOAD_BYTES,
    max_redirects=DEFAULT_MAX_REDIRECTS,
):
    """下载 URL 到临时文件，返回路径

    防护：仅允许 HTTPS；校验每一跳解析出的地址；限制重定向和下载大小。
    """
    current_url = url
    for redirect_count in range(max_redirects + 1):
        _validate_public_https_url(current_url)
        req = urllib.request.Request(
            current_url, headers={"User-Agent": "see-glm/1.0"}
        )
        try:
            response = _open_download_url(req, timeout=60)
        except urllib.error.HTTPError as e:
            if e.code not in (301, 302, 303, 307, 308):
                raise
            response = e

        with response as resp:
            status = resp.getcode()
            if status in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location")
                if not location:
                    raise ValueError(f"远程图片重定向缺少目标地址: {current_url}")
                if redirect_count >= max_redirects:
                    raise ValueError(
                        f"远程图片重定向次数超过上限 {max_redirects}: {url}"
                    )
                current_url = urllib.parse.urljoin(current_url, location)
                continue

            ctype = resp.headers.get("Content-Type", "")
            if ctype and not ctype.split(";")[0].strip().lower().startswith("image/"):
                print(
                    f"警告: {current_url} 的 Content-Type 为 {ctype}，可能不是图片",
                    file=sys.stderr,
                )
            data = bytearray()
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > max_bytes:
                    raise ValueError(
                        f"下载超过大小上限 {max_bytes // (1024 * 1024)}MB: {current_url}"
                    )
            final_url = current_url
            break
    else:
        raise ValueError(f"远程图片重定向次数超过上限 {max_redirects}: {url}")

    path_without_query = urllib.parse.urlparse(final_url).path
    suffix = "." + (
        path_without_query.split(".")[-1] if "." in path_without_query else "png"
    )
    if suffix.lstrip(".") not in SUPPORTED_EXT:
        suffix = ".png"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(data)
    tmp.close()
    return tmp.name


def file_to_base64(filepath):
    """文件转 base64，跨平台"""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ---- API 调用 ----
def clean_content(text):
    """清理 GLM thinking 模型返回的特殊 token（如 <|begin_of_box|>）"""
    return THINKING_TOKEN_PATTERN.sub("", text)


def call_glm_api(content_list, model, base_url, jwt_token, max_tokens=DEFAULT_MAX_TOKENS):
    """
    调用智谱 GLM API
    content_list: list of content items (text + image_url)
    返回: 模型回复文本（已清理特殊 token）
    """
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": content_list}],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return clean_content(data["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
            error_data = json.loads(error_body)
            error_msg = error_data.get("error", {}).get("message", error_body)
        except Exception:
            error_msg = error_body
        raise RuntimeError(f"API 请求失败 (HTTP {e.code}): {error_msg}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络请求失败: {e.reason}")


# ---- 构建请求内容 ----
def build_single_content(filepath, question):
    """为单张图构建 content 列表"""
    if is_url(filepath):
        return [
            {"type": "image_url", "image_url": {"url": filepath}},
            {"type": "text", "text": question}
        ]
    else:
        b64 = file_to_base64(filepath)
        mime = get_mime(filepath)
        return [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            {"type": "text", "text": question}
        ]


def build_together_content(filepaths, question):
    """为多图联合模式构建 content 列表"""
    content = []
    for fp in filepaths:
        if is_url(fp):
            content.append({"type": "image_url", "image_url": {"url": fp}})
        else:
            b64 = file_to_base64(fp)
            mime = get_mime(fp)
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    content.append({"type": "text", "text": question})
    return content


# ---- 结果输出 ----
def write_result(output_file, model, mode, files, results, together):
    """生成结果 Markdown"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# see-glm 分析结果",
        "",
        f"- **模型**: {model}",
        f"- **模式**: {mode}",
        f"- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **文件数**: {len(files)}",
        "",
        "---",
        "",
    ]
    if len(files) == 1:
        lines.append(f"## {files[0]}")
        lines.append("")
        lines.append(results[0])
    elif together:
        lines.append(f"## 联合分析 ({len(files)} 张图)")
        lines.append("")
        for i, f in enumerate(files):
            lines.append(f"**图 {i}: {f}**")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(results[0])
    else:
        for i, (f, r) in enumerate(zip(files, results)):
            lines.append(f"## {f}")
            lines.append("")
            lines.append(r)
            if i < len(results) - 1:
                lines.append("")
                lines.append("---")
                lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return str(output_path.resolve())


def fatal(message):
    """打印错误信息并退出（友好提示，避免裸 traceback）"""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


# ---- 主函数 ----
def main():
    parser = argparse.ArgumentParser(
        description="see-glm — 通过 GLM-4.1V-Thinking-Flash 查看图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 see.py screenshot.png
  python3 see.py a.png b.png
  python3 see.py --together before.png after.png --task "比较差异"
  python3 see.py screenshot.png --task "识别报错信息" -o result.md
        """
    )
    parser.add_argument("files", nargs="*", help="图片路径或 HTTPS URL")
    parser.add_argument("--onboard", action="store_true", help="快捷启动配置流程")
    parser.add_argument("--task", "-t", default="", help="自定义提问，原样发送给视觉模型")
    parser.add_argument("--together", action="store_true", help="多图联合理解模式")
    parser.add_argument("--jobs", "-j", type=int, default=DEFAULT_JOBS, help=f"并行并发数 (默认 {DEFAULT_JOBS})")
    parser.add_argument("--model", "-m", default="", help="临时覆盖模型")
    parser.add_argument("-o", "--output", default="", help="输出文件路径")
    args = parser.parse_args()

    # --onboard 快捷方式
    if args.onboard:
        subprocess.call([sys.executable, str(Path(__file__).parent / 'onboard.py')])
        return

    if not args.files:
        parser.print_help()
        sys.exit(1)

    # 加载配置
    config = load_config()
    api_key = config.get("GLM_API_KEY", "")
    base_url = config.get("GLM_BASE_URL", DEFAULT_BASE_URL)
    model = args.model or config.get("GLM_MODEL", DEFAULT_MODEL)
    # max_tokens: 可用 GLM_MAX_TOKENS 配置覆盖，非法值回退默认
    try:
        max_tokens = int(config.get("GLM_MAX_TOKENS") or DEFAULT_MAX_TOKENS)
    except (TypeError, ValueError):
        max_tokens = DEFAULT_MAX_TOKENS

    if not api_key:
        print("ERROR: 未配置 API Key", file=sys.stderr)
        print(f"请先运行: {sys.executable} {Path(__file__).name} --onboard", file=sys.stderr)
        print(f"或:      {sys.executable} {Path(__file__).parent / 'onboard.py'}", file=sys.stderr)
        sys.exit(1)

    # 生成 JWT
    jwt_token = generate_jwt(api_key)

    # 默认问题
    question = args.task or "请仔细观察这张图片，详细描述你看到的内容。如果有文字，请完整提取。"

    # 校验文件
    local_files = []  # (原始输入, 本地绝对路径, 是否为URL)
    tmp_files = []    # 需要清理的临时文件
    for f in args.files:
        try:
            resolved, is_net = validate_file(f)
            if is_net:
                print(f"正在下载: {f}...", file=sys.stderr)
                local_path = download_url(f)
                tmp_files.append(local_path)
                local_files.append((f, local_path, False))
            else:
                local_files.append((f, resolved, False))
        except (FileNotFoundError, ValueError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    # 输出文件
    if args.output:
        output_file = args.output
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False, prefix="see-glm-")
        tmp.close()
        output_file = tmp.name

    # ---- 执行分析 ----
    results = []
    mode = ""
    try:
        if args.together and len(local_files) > 1:
            # 联合模式
            mode = "联合理解"
            paths = [lf[1] for lf in local_files]
            content = build_together_content(paths, question)
            try:
                results.append(call_glm_api(content, model, base_url, jwt_token, max_tokens=max_tokens))
            except Exception as e:
                fatal(f"[分析失败] {local_files[0][0]}: {e}")
        elif len(local_files) == 1:
            # 单图模式
            mode = "单图分析"
            content = build_single_content(local_files[0][1], question)
            try:
                results.append(call_glm_api(content, model, base_url, jwt_token, max_tokens=max_tokens))
            except Exception as e:
                fatal(f"[分析失败] {local_files[0][0]}: {e}")
        else:
            # 并行模式
            mode = f"并行分析 ({args.jobs} 并发)"
            def analyze_one(item):
                orig, local_path, _ = item
                content = build_single_content(local_path, question)
                try:
                    return call_glm_api(content, model, base_url, jwt_token, max_tokens=max_tokens)
                except Exception as e:
                    return f"[分析失败] {orig}: {e}"
            # 每张图只提交一次；as_completed 不保序，用索引按输入顺序收集结果
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
                future_to_index = {
                    executor.submit(analyze_one, item): i
                    for i, item in enumerate(local_files)
                }
                results = [None] * len(local_files)
                for future in concurrent.futures.as_completed(future_to_index):
                    results[future_to_index[future]] = future.result()
    finally:
        # 清理临时文件
        for tf in tmp_files:
            try:
                os.unlink(tf)
            except OSError:
                pass

    # 写结果
    orig_names = [lf[0] for lf in local_files]
    result_path = write_result(output_file, model, mode, orig_names, results, args.together)
    # 唯一输出
    print(f"output_path={result_path}")


if __name__ == "__main__":
    main()
