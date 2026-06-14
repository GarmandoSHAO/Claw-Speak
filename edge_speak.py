#!/usr/bin/env python3
"""
Edge-TTS 静默朗读工具 v2

用微软 Edge 的 TTS 引擎合成语音并静默播放（Windows）。
依赖：pip install edge-tts soundfile

用法：
    python edge_speak.py --text "要朗读的文字"
    python edge_speak.py --text "你好" --voice zh-CN-XiaoxiaoNeural
    python edge_speak.py --list-voices
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import atexit
import winsound

# ─── 路径 ───────────────────────────────────────────────
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(TOOLS_DIR, "config.json")

# ─── 默认配置 ───────────────────────────────────────────
DEFAULT_CONFIG = {
    "python": "python3",
    "voice": "zh-CN-XiaoyiNeural",
    "proxy": "",
    "verbose": True,
}

def _log(msg):
    if DEFAULT_CONFIG.get("verbose", True):
        print(f"[Edge-TTS] {msg}", file=sys.stderr)

def load_config():
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                config.update(user_cfg)
            _log(f"已加载配置: {CONFIG_PATH}")
        except Exception as e:
            _log(f"加载配置失败: {e}")
    return config

CFG = load_config()

# ─── 代理 ────────────────────────────────────────────────
if CFG["proxy"]:
    os.environ["HTTP_PROXY"] = CFG["proxy"]
    os.environ["HTTPS_PROXY"] = CFG["proxy"]

# ─── 工具函数 ────────────────────────────────────────────
OUTPUT_DIR = os.path.join(TOOLS_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

_temp_files = []

def _cleanup():
    for f in _temp_files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except:
            pass

atexit.register(_cleanup)


def speak(text: str, voice: str = None) -> None:
    """合成语音 → 转 PCM WAV → 静默播放 → 自动清理"""
    voice = voice or CFG["voice"]
    python_bin = CFG["python"]

    # 第一步：edge-tts 合成（输出为 MP3 流）
    fd1, raw_path = tempfile.mkstemp(suffix=".mp3", dir=OUTPUT_DIR)
    os.close(fd1)
    _temp_files.append(raw_path)

    result = subprocess.run(
        [python_bin, "-m", "edge_tts",
         "--voice", voice,
         "--text", text,
         "--write-media", raw_path],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        _log(f"合成失败: {result.stderr}")
        return

    raw_size = os.path.getsize(raw_path)
    if raw_size < 100:
        _log(f"合成文件过小 ({raw_size} bytes)，跳过")
        return

    # 第二步：用 soundfile 转为标准 PCM WAV
    fd2, pcm_path = tempfile.mkstemp(suffix=".pcm.wav", dir=OUTPUT_DIR)
    os.close(fd2)
    _temp_files.append(pcm_path)

    conv = subprocess.run(
        [python_bin, "-c",
         "import soundfile as sf;"
         "import sys;"
         f"data, sr = sf.read(r'{raw_path}');"
         f"sf.write(r'{pcm_path}', data, sr, subtype='PCM_16');"
         "print('OK')"],
        capture_output=True, text=True, timeout=30
    )

    if "OK" not in conv.stdout:
        _log(f"格式转换失败: {conv.stderr}")
        return

    pcm_size = os.path.getsize(pcm_path)
    if pcm_size < 100:
        _log("PCM 文件过小，跳过")
        return

    # 第三步：播放 PCM WAV
    try:
        _log(f"播放 {pcm_size} bytes ({voice})...")
        winsound.PlaySound(pcm_path, winsound.SND_FILENAME)
    except Exception as e:
        _log(f"播放失败: {e}")


def list_voices():
    python_bin = CFG["python"]
    result = subprocess.run(
        [python_bin, "-m", "edge_tts", "--list-voices"],
        capture_output=True, text=True, timeout=30
    )
    for line in result.stdout.strip().split("\n"):
        if "CN" in line and "Female" in line:
            print(line)


def main():
    parser = argparse.ArgumentParser(description="Edge-TTS 静默朗读工具")
    parser.add_argument("--text", type=str, help="要朗读的文本")
    parser.add_argument("--voice", type=str, default=None, help="音色")
    parser.add_argument("--list-voices", action="store_true", help="列出可用声音")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if not args.text:
        print("错误: 请提供 --text")
        parser.print_help()
        return

    speak(args.text, voice=args.voice)


if __name__ == "__main__":
    main()
