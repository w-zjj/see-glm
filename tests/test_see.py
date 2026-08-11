"""see-glm 单元测试（无需真实 API Key，全部 mock）"""
import base64
import io
import json
import sys
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


def test_validate_file_url():
    path, is_net = see.validate_file("https://example.com/x.png")
    assert is_net and path == "https://example.com/x.png"


# ---- download_url ----
class _FakeResp:
    def __init__(self, data, headers):
        self._data = data
        self._pos = 0
        self.headers = headers

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, n=-1):
        if n < 0 or n is None:
            start = self._pos
            self._pos = len(self._data)
            return self._data[start:]
        chunk = self._data[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk


def test_download_url_normal(tmp_path, monkeypatch, capsys):
    payload = b"\x89PNG fake"
    fake = lambda *a, **k: _FakeResp(payload, {"Content-Type": "image/png"})
    monkeypatch.setattr(see.urllib.request, "urlopen", fake)
    path = see.download_url("https://example.com/a.png")
    try:
        assert Path(path).read_bytes() == payload
    finally:
        Path(path).unlink(missing_ok=True)
    assert "警告" not in capsys.readouterr().err


def test_download_url_size_limit(monkeypatch):
    payload = b"x" * 300
    fake = lambda *a, **k: _FakeResp(payload, {"Content-Type": "image/png"})
    monkeypatch.setattr(see.urllib.request, "urlopen", fake)
    with pytest.raises(ValueError, match="大小上限"):
        see.download_url("https://example.com/a.png", max_bytes=200)


def test_download_url_warns_on_non_image(monkeypatch, capsys):
    payload = b"<html>"
    fake = lambda *a, **k: _FakeResp(payload, {"Content-Type": "text/html"})
    monkeypatch.setattr(see.urllib.request, "urlopen", fake)
    path = see.download_url("https://example.com/x")
    try:
        assert Path(path).read_bytes() == payload
    finally:
        Path(path).unlink(missing_ok=True)
    assert "警告" in capsys.readouterr().err


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
