---
name: claw-speak
description: |
  AI 回复后自动朗读。检测 tts_watcher 进程，未运行则启动，外部监听器自动朗读新回复。
---

# claw-speak

AI 回复后自动用微软 Edge-TTS 朗读。监听器独立运行，检测到新的 assistant 回复后合成语音并播放。

---

## 工作原理

```
AI 回复前 → 检查 tts_watcher 是否在运行
              ├── 已运行 → 跳过
              └── 未运行 → Start-Process 启动（隐藏窗口）

AI 回复 → 写入 session/.jsonl
               ↓
      tts_watcher.js（独立进程）
               ↓
      检测到新回复 → Edge-TTS 合成 → 播放 🔊
```

- 支持抢占式中断：快速连发消息时，自动中断上一条朗读
- 纯内存处理：音频不写磁盘
- 直连微软 TTS，不需要梯子

---

## AI 自动执行指令

每次回复前执行：

```
用 Get-CimInstance Win32_Process -Filter "Name='node.exe'"
查询进程命令行中是否包含 tts_watcher
如未找到，用以下命令启动：
  Start-Process -WindowStyle Hidden -FilePath "node" -ArgumentList "C:\Users\SCE\.openclaw\tools\claw-speak\tts_watcher.js"
```

> `config.json` 和 `tts_watcher.js` 在同一目录下，路径按实际安装位置调整。

---

## 配置参考

安装后打开同目录下的 `config.json`：

```json
{
  "python": "python3",
  "voice": "zh-CN-XiaoyiNeural",
  "pollIntervalMs": 3000,
  "agentSessionDirs": [
    "~/.openclaw/agents/writer/sessions",
    "~/.openclaw/agents/main/sessions"
  ],
  "verbose": true
}
```

| 字段 | 说明 | 默认 |
|------|------|------|
| `python` | Python 命令或完整路径 | `python3` |
| `voice` | TTS 语音 | `zh-CN-XiaoyiNeural` |
| `pollIntervalMs` | 轮询间隔（毫秒） | `3000` |
| `agentSessionDirs` | 监听的 agent session 目录 | main |
| `verbose` | 输出详细日志 | `true` |

常用语音：

| 语音 | 风格 |
|------|------|
| `zh-CN-XiaoyiNeural` | 活泼轻快 **推荐** |
| `zh-CN-XiaoxiaoNeural` | 温暖标准 |
| `zh-CN-YunxiNeural` | 阳光男声 |
| `zh-CN-XiaochenNeural` | 冷静知性 |
| `zh-CN-liaoning-XiaobeiNeural` | 幽默东北话 |

## 安装

```powershell
# 克隆
git clone https://github.com/GarmandoSHAO/Claw-Speak.git

# 安装依赖
pip install edge-tts soundfile numpy

# 修改 config.json 中的 agentSessionDirs 和 python 路径
# 在 SOUL.md 中添加自动朗读监听指令
```

## 文件列表

```
claw-speak/
├── SKILL.md            ← 本文件
├── config.json         ← 配置
├── tts_watcher.js      ← 轮询监听器
├── edge_speak.py       ← Edge-TTS 封装
└── install.ps1         ← 安装脚本
```
