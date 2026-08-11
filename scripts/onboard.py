#!/usr/bin/env python3
"""
see-glm onboard script
交互式配置 GLM API Key，保存到用户私有目录。
跨平台: Windows (APPDATA) / macOS Linux (~/.config)
"""

import os
import sys
from pathlib import Path

DEFAULT_MODEL = "GLM-4.1V-Thinking-Flash"
DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"


def get_config_dir():
    """跨平台配置目录"""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", "")
        if base:
            return Path(base) / "see-glm"
        return Path.home() / ".config" / "see-glm"
    else:
        return Path.home() / ".config" / "see-glm"


CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.env"


def get_config():
    """读取已有配置"""
    config = {}
    if CONFIG_FILE.is_file():
        for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    return config


def save_config(config):
    """保存配置到文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = "# see-glm 配置文件\n"
    content += "# 此文件由 onboard.py 生成，请勿提交到 Git\n"
    content += "# 优先级：环境变量 > 项目 .env.local > 此文件\n\n"
    for key, value in config.items():
        if value:
            content += f"{key}={value}\n"
    CONFIG_FILE.write_text(content, encoding="utf-8")

    # Unix 系统限制权限为 600
    if sys.platform != "win32":
        os.chmod(str(CONFIG_FILE), 0o600)

    print(f"配置已保存到: {CONFIG_FILE}")


def show_status(config):
    """显示当前配置状态"""
    print("\n=== see-glm 配置状态 ===\n")

    api_key = config.get("GLM_API_KEY", "")
    base_url = config.get("GLM_BASE_URL", DEFAULT_BASE_URL)
    model = config.get("GLM_MODEL", DEFAULT_MODEL)

    # 也检查环境变量
    env_key = os.environ.get("GLM_API_KEY", "")

    if env_key:
        print(f"API Key:    [环境变量] {env_key[:8]}...{env_key[-4:]}")
        print(f"            (环境变量优先级最高)")
    elif api_key:
        print(f"API Key:    [配置文件] {api_key[:8]}...{api_key[-4:]}")
        print(f"            配置文件: {CONFIG_FILE}")
    else:
        print(f"API Key:    未配置")

    print(f"Base URL:   {base_url}")
    print(f"模型:       {model}")
    print(f"Python:     {sys.version.split()[0]}")
    print(f"系统:       {sys.platform}")
    print(f"配置目录:   {CONFIG_DIR}")

    if not env_key and not api_key:
        print(f"\n尚未配置 API Key，请运行: python3 scripts/onboard.py")
    else:
        print(f"\n配置就绪，可以直接使用 see.py")


def run_onboard():
    """交互式配置流程"""
    print("\n=== see-glm 安装配置 ===")
    print(f"视觉模型: {DEFAULT_MODEL}")
    print(f"API 地址: {DEFAULT_BASE_URL}")
    print(f"配置保存: {CONFIG_FILE}")
    print()

    # 读取已有配置
    existing = get_config()

    # API Key
    print("请输入你的智谱 API Key")
    print("(格式: xxxxxx.xxxxxx，可在 https://open.bigmodel.cn 获取)")
    if existing.get("GLM_API_KEY"):
        print(f"当前已配置: {existing['GLM_API_KEY'][:8]}...{existing['GLM_API_KEY'][-4:]}")
        print("直接回车保留当前 Key，输入新 Key 则替换")

    api_key = input("API Key: ").strip()
    if not api_key and existing.get("GLM_API_KEY"):
        api_key = existing["GLM_API_KEY"]

    if not api_key:
        print("\n未输入 API Key，配置未保存。")
        print("没有 API Key 将无法使用云端视觉分析。")
        sys.exit(1)

    # 验证 Key 格式（简单检查）
    if "." not in api_key or len(api_key) < 10:
        print(f"\nKey 格式可能不正确，智谱 API Key 通常包含点号分隔的两段。")
        print(f"   你的输入: {api_key[:8]}...")
        confirm = input("仍然保存？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            sys.exit(0)

    # Base URL
    print(f"\nAPI 地址 (默认: {DEFAULT_BASE_URL})")
    base_url = input("> ").strip() or DEFAULT_BASE_URL

    # Model
    print(f"\n模型名称 (默认: {DEFAULT_MODEL})")
    model = input("> ").strip() or DEFAULT_MODEL

    # 保存
    config = {
        "GLM_API_KEY": api_key,
        "GLM_BASE_URL": base_url,
        "GLM_MODEL": model,
    }
    save_config(config)

    print("\n配置完成！现在可以使用 see.py 查看图片了。")
    print(f"   示例: python3 scripts/see.py C:/Users/me/Desktop/screenshot.png")


def main():
    if "--status" in sys.argv:
        config = get_config()
        show_status(config)
    else:
        run_onboard()


if __name__ == "__main__":
    main()
