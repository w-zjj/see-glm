"""see-glm 单元测试（无需真实 API Key，全部 mock）"""
import base64
import io
import json
import subprocess
import sys
import socket
from pathlib import Path
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import see  # noqa: E402


# ---- generate_jwt ----
def test_generate_jwt_dotted_key():
    token = see.generate_jwt("id123.secret456")
    parts = token.split(".")
    assert len(parts) == 3
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    assert header["alg"] == "HS256"
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    assert payload["api_key"] == "id123"
    assert payload["exp"] == payload["timestamp"] + 3600


def test_generate_jwt_plain_key_passthrough():
    assert see.generate_jwt("plain-no-dot-key") == "plain-no-dot-key"


# ---- clean_content ----
def test_clean_content_removes_thinking_tokens():
    text = "正常内容<|begin_of_box|><|endofthought|>尾巴"
    assert see.clean_content(text) == "正常内容尾巴"


# ---- 工具函数 ----
def test_is_url():
    assert see.is_url("https://example.com/a.png")
    assert see.is_url("http://example.com/a.png")
    assert not see.is_url("local.png")
    assert not see.is_url("C:\\a.png")


def test_get_ext():
    assert see.get_ext("a.PNG") == "png"
    assert see.get_ext("b.jpeg") == "jpeg"


def test_get_mime():
    assert see.get_mime("a.png") == "image/png"
    assert see.get_mime("unknown.xyz") == "image/png"


def test_validate_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        see.validate_file(str(tmp_path / "nope.png"))


def test_validate_file_unsupported(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF")
    with pytest.raises(ValueError):
        see.validate_file(str(f))


@pytest.mark.parametrize(
    ("filename", "payload"),
    [
        ("a.png", b"\x89PNG\r\n\x1a\n"),
        ("a.jpg", b"\xff\xd8\xff\xe0"),
        ("a.jpeg", b"\xff\xd8\xff\xe0"),
        ("a.gif", b"GIF89a"),
        ("a.webp", b"RIFFxxxxWEBP"),
        ("a.bmp", b"BM\x00\x00"),
    ],
)
def test_validate_file_accepts_supported_real_formats(tmp_path, filename, payload):
    path = tmp_path / filename
    path.write_bytes(payload)
    resolved, is_net = see.validate_file(str(path))
    assert Path(resolved) == path.resolve()
    assert not is_net


def test_validate_file_rejects_fake_extension(tmp_path):
    path = tmp_path / "fake.png"
    path.write_bytes(b"<html>not an image</html>")
    with pytest.raises(ValueError, match="无法识别图片真实格式"):
        see.validate_file(str(path))


def test_validate_file_rejects_extension_mismatch(tmp_path):
    path = tmp_path / "fake.png"
    path.write_bytes(b"GIF89a")
    with pytest.raises(ValueError, match="真实格式与扩展名不一致"):
        see.validate_file(str(path))


def test_validate_file_url():
    path, is_net = see.validate_file("https://example.com/x.png")
    assert is_net and path == "https://example.com/x.png"


# ---- download_url ----
class _FakeResp:
    def __init__(self, data, headers, status=200):
        self._data = data
        self._pos = 0
        self.headers = headers
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def getcode(self):
        return self.status

    def read(self, n=-1):
        if n < 0 or n is None:
            start = self._pos
            self._pos = len(self._data)
            return self._data[start:]
        chunk = self._data[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk


def test_download_url_normal(tmp_path, monkeypatch, capsys):
    payload = b"\x89PNG\r\n\x1a\nfake"
    fake = lambda *a, **k: _FakeResp(payload, {"Content-Type": "image/png"})
    monkeypatch.setattr(see, "_open_download_url", fake)
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )
    path = see.download_url("https://example.com/a.png")
    try:
        assert Path(path).read_bytes() == payload
    finally:
        Path(path).unlink(missing_ok=True)
    assert "警告" not in capsys.readouterr().err


def test_download_url_size_limit(monkeypatch):
    payload = b"x" * 300
    fake = lambda *a, **k: _FakeResp(payload, {"Content-Type": "image/png"})
    monkeypatch.setattr(see, "_open_download_url", fake)
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )
    with pytest.raises(ValueError, match="大小上限"):
        see.download_url("https://example.com/a.png", max_bytes=200)


def test_download_url_warns_on_non_image(monkeypatch, capsys):
    payload = b"<html>"
    fake = lambda *a, **k: _FakeResp(payload, {"Content-Type": "text/html"})
    monkeypatch.setattr(see, "_open_download_url", fake)
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )
    with pytest.raises(ValueError, match="无法识别远程图片真实格式"):
        see.download_url("https://example.com/x")
    assert "警告" in capsys.readouterr().err


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/a.png",
        "https://localhost/a.png",
        "https://127.0.0.1/a.png",
        "https://[::1]/a.png",
    ],
)
def test_download_url_rejects_unsafe_urls(url, monkeypatch):
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(ValueError, match="(HTTPS|受限网络地址)"):
        see.download_url(url)


def test_download_url_rejects_private_dns_result(monkeypatch):
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.7", 443))
        ],
    )
    with pytest.raises(ValueError, match="受限网络地址"):
        see.download_url("https://public.example/a.png")


def test_download_url_validates_redirect_target(monkeypatch):
    calls = []

    def fake_open(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            return _FakeResp(
                b"", {"Location": "https://127.0.0.1/secret"}, status=302
            )
        return _FakeResp(b"\x89PNG", {"Content-Type": "image/png"})

    def fake_resolve(host, port, *args, **kwargs):
        address = "93.184.216.34" if host == "public.example" else "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    monkeypatch.setattr(see, "_open_download_url", fake_open)
    monkeypatch.setattr(see.socket, "getaddrinfo", fake_resolve)
    with pytest.raises(ValueError, match="受限网络地址"):
        see.download_url("https://public.example/a.png")
    assert calls == ["https://public.example/a.png"]


def test_download_url_limits_redirects(monkeypatch):
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )
    monkeypatch.setattr(
        see,
        "_open_download_url",
        lambda *a, **k: _FakeResp(
            b"", {"Location": "https://public.example/a.png"}, status=302
        ),
    )
    with pytest.raises(ValueError, match="重定向次数超过上限"):
        see.download_url("https://public.example/a.png", max_redirects=2)


def test_download_url_preserves_non_redirect_http_errors(monkeypatch):
    monkeypatch.setattr(
        see.socket,
        "getaddrinfo",
        lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )

    def boom(*a, **k):
        raise HTTPError("https://public.example/a.png", 404, "Not Found", {}, io.BytesIO())

    monkeypatch.setattr(see, "_open_download_url", boom)
    with pytest.raises(HTTPError):
        see.download_url("https://public.example/a.png")


# ---- call_glm_api ----
def test_call_glm_api_success(monkeypatch):
    body = {"choices": [{"message": {"content": "结果<|thought|>去敏"}}]}
    fake = lambda *a, **k: _FakeResp(json.dumps(body).encode(), {})
    monkeypatch.setattr(see.urllib.request, "urlopen", fake)
    out = see.call_glm_api([], "m", "https://x", "token")
    assert out == "结果去敏"


def test_call_glm_api_http_error(monkeypatch):
    def boom(*a, **k):
        raise HTTPError(
            "https://x", 429, "Too Many Requests", {},
            io.BytesIO(b'{"error":{"message":"rate limited"}}'),
        )
    monkeypatch.setattr(see.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError, match="rate limited"):
        see.call_glm_api([], "m", "https://x", "token")


# ---- 构建 content ----
def test_build_single_content_local(tmp_path):
    f = tmp_path / "p.png"
    f.write_bytes(b"\x89PNG")
    content = see.build_single_content(str(f), "q")
    assert content[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert content[1]["text"] == "q"


def test_file_to_base64_rejects_oversized_image(tmp_path):
    f = tmp_path / "large.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 100)
    with pytest.raises(ValueError, match="图片超过大小上限"):
        see.file_to_base64(str(f), max_bytes=50)


def test_build_single_content_url():
    content = see.build_single_content("https://e.com/a.png", "q")
    assert content[0]["image_url"]["url"] == "https://e.com/a.png"


def test_build_together_content(tmp_path):
    f1 = tmp_path / "a.png"
    f1.write_bytes(b"\x89PNG")
    content = see.build_together_content(["https://e.com/b.jpg", str(f1)], "diff")
    assert content[0]["image_url"]["url"] == "https://e.com/b.jpg"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert content[2]["text"] == "diff"


def test_call_glm_api_rejects_oversized_request(monkeypatch):
    content = [{"type": "text", "text": "x" * 1000}]
    with pytest.raises(ValueError, match="API 请求体超过大小上限"):
        see.call_glm_api(
            content,
            "m",
            "https://x",
            "token",
            max_request_bytes=100,
        )


# ---- load_config ----
def test_load_config_priority(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    (cfg_dir / "config.env").write_text(
        "GLM_API_KEY=from-config\nGLM_MODEL=m1\n", encoding="utf-8"
    )
    monkeypatch.setattr(see, "get_config_dir", lambda: cfg_dir)
    # 环境变量优先级最高
    monkeypatch.setenv("GLM_API_KEY", "from-env")
    cfg = see.load_config()
    assert cfg["GLM_API_KEY"] == "from-env"
    assert cfg["GLM_MODEL"] == "m1"


def test_call_glm_api_retries_rate_limit_and_honors_retry_after(monkeypatch):
    attempts = []
    delays = []
    response_body = {"choices": [{"message": {"content": "ok"}}]}

    def fake_urlopen(request, *args, **kwargs):
        attempts.append(request)
        if len(attempts) == 1:
            raise HTTPError(
                "https://x",
                429,
                "Too Many Requests",
                {"Retry-After": "2"},
                io.BytesIO(b'{"error":{"message":"rate limited"}}'),
            )
        return _FakeResp(json.dumps(response_body).encode(), {})

    monkeypatch.setattr(see.urllib.request, "urlopen", fake_urlopen)
    result = see.call_glm_api(
        [], "m", "https://x", "token", max_retries=2, sleep=delays.append
    )
    assert result == "ok"
    assert len(attempts) == 2
    assert delays == [2.0]


def test_call_glm_api_does_not_retry_auth_error(monkeypatch):
    attempts = []

    def fake_urlopen(request, *args, **kwargs):
        attempts.append(request)
        raise HTTPError(
            "https://x",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error":{"message":"bad key"}}'),
        )

    monkeypatch.setattr(see.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="bad key"):
        see.call_glm_api(
            [], "m", "https://x", "token", max_retries=3, sleep=lambda _: None
        )
    assert len(attempts) == 1


def test_default_model_is_glm_46v_flash():
    assert see.DEFAULT_MODEL == "glm-4.6v-flash"


def test_call_glm_api_includes_thinking_mode(monkeypatch):
    response_body = {"choices": [{"message": {"content": "ok"}}]}
    captured = {}

    def fake_urlopen(request, *args, **kwargs):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResp(json.dumps(response_body).encode(), {})

    monkeypatch.setattr(see.urllib.request, "urlopen", fake_urlopen)
    assert see.call_glm_api(
        [], "glm-4.6v-flash", "https://x", "token", thinking="enabled"
    ) == "ok"
    assert captured["body"]["thinking"] == {"type": "enabled"}


@pytest.mark.parametrize("jobs", ["0", "-1", "65"])
def test_jobs_out_of_range_rejected(jobs):
    script = Path(__file__).resolve().parent.parent / "scripts" / "see.py"
    result = subprocess.run(
        [sys.executable, str(script), "missing.png", "--jobs", jobs],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


@pytest.mark.parametrize("jobs", ["1", "3", "64"])
def test_jobs_in_range_reaches_file_validation(jobs):
    script = Path(__file__).resolve().parent.parent / "scripts" / "see.py"
    result = subprocess.run(
        [sys.executable, str(script), "missing.png", "--jobs", jobs],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "invalid choice" not in result.stderr
    assert "missing.png" in result.stderr


@pytest.mark.parametrize("allow_partial, expected_code", [(False, 2), (True, None)])
def test_parallel_failure_policy_writes_partial_results(
    tmp_path, monkeypatch, capsys, allow_partial, expected_code
):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"\x89PNG\r\n\x1a\n")
    second.write_bytes(b"\x89PNG\r\n\x1a\n")
    output = tmp_path / "result.md"

    def fake_validate_file(filepath):
        return str(Path(filepath).resolve()), False

    def fake_build_content(filepath, question):
        return [{"path": Path(filepath).name}]

    def fake_call(content, *args, **kwargs):
        if content[0]["path"] == "second.png":
            raise RuntimeError("temporary failure")
        return "first result"

    monkeypatch.setattr(see, "load_config", lambda: {"GLM_API_KEY": "token"})
    monkeypatch.setattr(see, "validate_file", fake_validate_file)
    monkeypatch.setattr(see, "build_single_content", fake_build_content)
    monkeypatch.setattr(see, "call_glm_api", fake_call)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "see.py",
            str(first),
            str(second),
            "--jobs",
            "2",
            "--output",
            str(output),
        ]
        + (["--allow-partial"] if allow_partial else []),
    )

    if expected_code is None:
        see.main()
    else:
        with pytest.raises(SystemExit) as exc_info:
            see.main()
        assert exc_info.value.code == expected_code

    assert output.is_file()
    text = output.read_text(encoding="utf-8")
    assert "first result" in text
    assert "[分析失败]" in text
    assert "1/2" in capsys.readouterr().err
