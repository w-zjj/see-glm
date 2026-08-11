#!/usr/bin/env python3
"""
see-glm 媒体文件处理工具
提供文件校验、格式检测、base64 编码等功能，
供 see.sh 和其他脚本调用。
用法:
  python3 parse_media.py validate /path/to/image.png
  python3 parse_media.py base64 /path/to/image.png
  python3 parse_media.py mime /path/to/image.png
  python3 parse_media.py info /path/to/image.png
"""
import os
import sys
import base64
import json
import struct

SUPPORTED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
}


def get_ext(filepath):
    """获取文件扩展名（小写）"""
    return os.path.splitext(filepath)[1].lstrip(".").lower()


def get_mime(filepath):
    """根据扩展名获取 MIME 类型"""
    ext = get_ext(filepath)
    return MIME_MAP.get(ext, "image/png")


def is_url(s):
    """判断字符串是否为 HTTP(S) URL"""
    return s.startswith("http://") or s.startswith("https://")


def validate(filepath):
    """校验文件是否存在且格式支持"""
    if is_url(filepath):
        print(json.dumps({"valid": True, "type": "url", "path": filepath}))
        return True
    if not os.path.isfile(filepath):
        print(json.dumps({"valid": False, "error": f"文件不存在: {filepath}"}))
        return False
    ext = get_ext(filepath)
    if ext not in SUPPORTED_EXT:
        print(json.dumps({
            "valid": False,
            "error": f"不支持的格式 .{ext}，仅支持: {', '.join(sorted(SUPPORTED_EXT))}"
        }))
        return False
    size = os.path.getsize(filepath)
    print(json.dumps({
        "valid": True,
        "type": "local",
        "path": os.path.abspath(filepath),
        "ext": ext,
        "mime": get_mime(filepath),
        "size_bytes": size,
        "size_mb": round(size / 1024 / 1024, 2),
    }))
    return True


def to_base64(filepath):
    """将文件编码为 base64 字符串"""
    if not os.path.isfile(filepath):
        print(json.dumps({"error": f"文件不存在: {filepath}"}))
        return False
    mime = get_mime(filepath)
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    print(json.dumps({
        "mime": mime,
        "base64": data,
        "data_url": f"data:{mime};base64,{data}",
        "size_bytes": len(data),
    }))
    return True


def file_info(filepath):
    """输出文件详细信息"""
    if not os.path.isfile(filepath):
        print(json.dumps({"error": f"文件不存在: {filepath}"}))
        return False
    ext = get_ext(filepath)
    size = os.path.getsize(filepath)
    mime = get_mime(filepath)
    info = {
        "path": os.path.abspath(filepath),
        "name": os.path.basename(filepath),
        "ext": ext,
        "mime": mime,
        "size_bytes": size,
        "size_mb": round(size / 1024 / 1024, 2),
    }
    # 尝试获取图片尺寸（仅 PNG、BMP）
    try:
        if ext == "png":
            with open(filepath, "rb") as f:
                f.read(8)  # skip PNG signature
                f.read(4)  # skip length
                chunk_type = f.read(4)
                if chunk_type == b"IHDR":
                    width = struct.unpack(">I", f.read(4))[0]
                    height = struct.unpack(">I", f.read(4))[0]
                    info["width"] = width
                    info["height"] = height
    except Exception:
        pass
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return True


def main():
    if len(sys.argv) < 3:
        print("用法: parse_media.py <command> <filepath>")
        print("命令: validate, base64, mime, info")
        sys.exit(1)
    command = sys.argv[1]
    filepath = sys.argv[2]
    commands = {
        "validate": lambda: validate(filepath),
        "base64": lambda: to_base64(filepath),
        "mime": lambda: print(get_mime(filepath)),
        "info": lambda: file_info(filepath),
    }
    fn = commands.get(command)
    if fn is None:
        print(f"未知命令: {command}")
        print("可用命令: validate, base64, mime, info")
        sys.exit(1)
    fn()


if __name__ == "__main__":
    main()
