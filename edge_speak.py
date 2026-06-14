#!/usr/bin/env python3
"""
Edge-TTS 静默朗读工具 v3

用微软 Edge 的 TTS 引擎合成语音并静默播放（Windows）。
不保存任何音频文件到磁盘，全部在内存中处理。

依赖：pip install edge-tts soundfile numpy

用法：
    python edge_speak.py --text "要朗读的文字"
    python edge_speak.py --text "你好" --voice zh-CN-XiaoxiaoNeural
    python edge_speak.py --list-voices
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
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


def speak(text: str, voice: str = None) -> None:
    """合成语音 → 内存转 PCM → 内存播放，全程不落盘"""
    voice = voice or CFG["voice"]
    python_bin = CFG["python"]

    # 临时 MP3 路径（仅边角料，播完即删）
    fd, raw_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    try:
        # 第一步：edge-tts 合成（不得已写磁盘，仅此一步）
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

        # 第二步：用 soundfile 从 MP3 读取到内存
        import soundfile as sf

        data, sr = sf.read(raw_path)
        if len(data) == 0:
            _log("读取音频数据为空，跳过")
            return

        # 第三步：内存中转为标准 PCM WAV
        buf = io.BytesIO()
        sf.write(buf, data, sr, subtype="PCM_16", format="WAV")
        pcm_data = buf.getvalue()

        # 第四步：内存播放
        _log(f"播放 {raw_size} bytes → PCM {len(pcm_data)} bytes ({voice})...")
        winsound.PlaySound(pcm_data, winsound.SND_MEMORY)
        _log("播放完成")

    except Exception as e:
        _log(f"播放失败: {e}")
    finally:
        # 立即删除唯一落盘的临时文件
        try:
            if os.path.exists(raw_path):
                os.remove(raw_path)
        except Exception:
            pass


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
    parser = argparse.ArgumentParser(description="Edge-TTS 静默朗读工具（纯内存，不落盘）")
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
