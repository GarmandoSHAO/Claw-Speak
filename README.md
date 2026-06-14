# claw-speak 🎙️

**OpenClaw 自动 TTS 朗读工具** — AI 回复时自动用微软 Edge-TTS 活泼女声朗读。

自动监听 OpenClaw Agent 的 session 文件，检测到新的 AI 回复立即朗读，全程无需人工干预。

---

## 原理

```
OpenClaw Agent 回复
       ↓
  ┌─ tts_watcher.js ───────────────────────┐
  │  每 6 秒轮询 session/.jsonl 文件        │
  │  检测到新 assistant 回复 → 提取纯文本    │
  │  去除 Markdown / 代码块 / 链接等        │
  └──────────┬──────────────────────────────┘
             ↓
  ┌─ edge_speak.py ─────────────────────────┐
  │  Edge-TTS 合成语音                      │
  │  → PCM WAV 转换                         │
  │  → winsound 静默播放                    │
  └──────────────────────────────────────────┘
             ↓
        扬声器朗读 🔊
```

---

## 快速开始

### 前置要求

| 依赖 | 说明 |
|------|------|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) |
| **Node.js** | [nodejs.org](https://nodejs.org/) |
| **OpenClaw** | [openclaw.ai](https://openclaw.ai) |

### 安装

```powershell
# 一键安装
.\install.ps1

# 或手动安装依赖
pip install edge-tts soundfile numpy
```

### 配置

安装完成后，修改 `config.json` 文件来配置您的 Agent：

```json
{
  "python": "python3",
  "voice": "zh-CN-XiaoyiNeural",
  "pollIntervalMs": 6000,
  "agentSessionDirs": [
    "~/.openclaw/agents/main/sessions"
  ],
  "proxy": "http://127.0.0.1:7890",
  "verbose": true
}
```

**关键配置说明：**

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `agentSessionDirs` | **必填** — 监听的 agent session 目录列表 | main |
| `voice` | TTS 语音类型 | `zh-CN-XiaoyiNeural` |
| `pollIntervalMs` | 轮询间隔（毫秒） | `6000` |
| `python` | Python 可执行路径 | `python3` |
| `proxy` | HTTP 代理（留空 = 不走代理） | Clash 默认 |
| `verbose` | 是否输出详细日志 | `true` |

**多 Agent 配置示例：**

如果您的 OpenClaw 有多个 agent（如 main、shiori、writer），在 `agentSessionDirs` 中列出所有目录：

```json
{
  "agentSessionDirs": [
    "~/.openclaw/agents/writer/sessions",
    "~/.openclaw/agents/main/sessions",
    "~/.openclaw/agents/shiori/sessions"
  ]
}
```

### 启动

```powershell
# 启动监听器
node tts_watcher.js
```

启动后，监听器会在后台自动工作。当 AI 回复时，你会听到语音朗读。

### 停止

按 `Ctrl+C` 停止监听。

---

## 可用语音

| 语音 | 风格 | 适用场景 |
|------|------|----------|
| `zh-CN-XiaoyiNeural` | 活泼轻快 ✅ **推荐** | 日常/故事/网文 |
| `zh-CN-XiaoxiaoNeural` | 温暖标准 | 新闻/小说/正式 |
| `zh-CN-liaoning-XiaobeiNeural` | 幽默 | 方言/东北话 |
| `zh-CN-shaanxi-XiaoniNeural` | 明亮 | 方言/陕西话 |

列出所有中文女声：

```powershell
python edge_speak.py --list-voices
```

---

## 作为 OpenClaw Skill 使用

该工具可作为 OpenClaw Skill 自动守护：每次 AI 回复前检查监听器是否运行，未运行则自动启动。

需要将 `claw-speak` Skill 安装到 OpenClaw 中（参见 Skill Workshop 提案）。

---

## 目录结构

```
claw-speak/
├── README.md            ← 本文件
├── SKILL.md             ← OpenClaw Skill 文件
├── install.ps1          ← 一键安装脚本
├── config.example.json  ← 配置文件示例
├── config.json          ← 实际配置（自动生成）
├── tts_watcher.js       ← 轮询监听器（核心）
├── edge_speak.py        ← Edge-TTS 引擎封装（核心）
├── assets/              ← 资源/测试音频
└── output/              ← 临时音频输出
```

---

## 许可证

MIT

## 相关链接

- [Edge-TTS](https://github.com/rany2/edge-tts) — 微软 Edge 在线阅读 TTS 引擎
- [OpenClaw](https://openclaw.ai) — AI Agent 框架
