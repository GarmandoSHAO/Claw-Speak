# claw-speak v3

**OpenClaw Skill** —— AI 回复后自动用微软 Edge-TTS 读出声音来。

这不是独立工具，而是一个 OpenClaw Skill。AI Agent 在每次回复前自动检查 TTS 监听器是否在运行，没运行就自己启动，然后外部监听器检测到新回复立即朗读。

> 读完本文件、按步骤走完配置，之后每次 OpenClaw 回复你都能直接听到声音。

---

## 架构一览

```
你发消息 → OpenClaw AI
              │
              ├── 回复前：执行 claw-speak Skill
              │     ├── 检查 tts_watcher 是否在运行
              │     └── 未运行则自动启动（隐藏窗口）
              │
              ├── AI 生成回复 → 写入 session/.jsonl
              │
              └── tts_watcher.js（独立进程）
                    └── 轮询检测到新回复
                          ├── 中断当前朗读（如有）
                          └── Edge-TTS 合成语音 → 内存播放 🔊
```

关键点：**人不需要手动启停**。Agent 自身负责管理监听器的生命周期。

---

## 特性和约束

| 特性 | 说明 |
|------|------|
| **抢占式中断** | 快速连发两条消息时，自动中断上一条朗读，直接读最新的 |
| **多 Agent** | 一个监听器同时监听多个 agent |
| **纯内存处理** | 音频全程在内存中合成转换，不写磁盘 |
| **直连微软 TTS** | 不需要梯子/代理，直连云服务 |
| **零窗口干扰** | 纯命令行后台运行，不弹任何窗口 |

---

## 完整部署步骤

### 第一步：获取文件

把整个 `claw-speak/` 目录放到你的 OpenClaw 环境里，推荐位置：

```
~/.openclaw/tools/claw-speak/
```

> 如果是从仓库克隆：
> ```powershell
> git clone <仓库地址> ~/.openclaw/tools/claw-speak/
> ```

---

### 第二步：检查依赖

| 依赖 | 最低版本 | 用途 |
|------|---------|------|
| **Node.js** | v18+ | 运行 tts_watcher 监听器 |
| **Python** | 3.10+ | 运行语音合成 |

确认：
```powershell
node --version
python --version
```

---

### 第三步：安装 Python 包

```powershell
pip install edge-tts soundfile numpy
```

---

### 第四步：修改配置

打开 `config.json`，填入你的实际信息。

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

| 字段 | 说明 | 示例 |
|------|------|------|
| `python` | Python 命令名或完整路径 | `"python3"` 或 `"C:\\Python312\\python.exe"` |
| `agentSessionDirs` | **必填** — 监听哪些 agent 的回复 | 见上 |
| `voice` | TTS 语音 | `"zh-CN-XiaoyiNeural"`（推荐） |
| `pollIntervalMs` | 轮询间隔（毫秒） | `3000`（3秒） |
| `verbose` | 是否输出日志 | `true` |

注意：**不需要 `proxy` 字段**。Edge-TTS 直连云，无需梯子。

---

### 第五步：确定要监听的 Agent

```powershell
dir ~/.openclaw/agents/*/sessions/
```

常见的 agent：
- `main` — 默认主 agent
- `writer` — 写作 agent
- `shiori` — 其他 agent

把你要监听的那些目录名写入 `config.json` 的 `agentSessionDirs` 数组。

---

### 第六步：让 AI 知道这个 Skill

在 agent 的 `SOUL.md` 或 `AGENTS.md` 中添加以下指令：

```
**自动朗读监听**：每次回复前，检查 TTS 监听器是否运行。
检查方法：Get-CimInstance 查询 node.exe 进程命令行中是否包含 tts_watcher。
如未运行，用 Start-Process -WindowStyle Hidden 启动 tts_watcher.js。
```

---

### 第七步：验证是否工作

1. 给你的 OpenClaw agent 发一条消息
2. AI 回复时，后台自动启动 tts_watcher（如果没在运行）
3. 回复生成后几秒内，你应该听到扬声器出声

**排查清单：**
- 扬声器没静音？
- `agentSessionDirs` 路径写对了？agent 名字大小写一致？
- Python 依赖装全了？`pip list | findstr edge-tts`
- tts_watcher.js 的路径写对了？

---

## 运行机制详解

### 正常流程

```
用户发消息
    │
    ▼
AI 准备回复
    │
    ├── 执行 Skill 指令
    │     ├── Get-CimInstance 查 tts_watcher 进程
    │     ├── 没找到 → Start-Process 启动
    │     └── 已在运行 → 跳过
    │
    ├── AI 生成回复，写入 session/.jsonl
    │
    ▼
tts_watcher.js（外部独立进程，已就绪）
    │
    ├── 轮询检测到新的 assistant 回复
    ├── 去除 Markdown/代码块/链接，提取纯文本
    ├── 如果正在朗读 → 中断（抢占式）
    ├── 调用 edge_speak.py
    │
    ▼
edge_speak.py（纯内存处理，不写磁盘）
    │
    ├── Edge-TTS 合成 MP3（临时文件，播完即删）
    ├── soundfile 读到内存
    ├── 内存转 PCM WAV → BytesIO
    └── winsound 内存播放 SND_MEMORY 🔊
```

### 抢占式中断

快速连发两条消息时，AI 分别回复。tts_watcher 检测到新回复后会：

1. 立即 `kill()` 正在朗读的进程
2. 启动新进程朗读最新回复
3. 不会出现两段语音重叠

### 多 Agent 支持

监听器同时监听多个 agent，始终朗读最新检测到的回复。

---

## 进程管理（手动）

正常情况不需要手动操作，AI 会自动管理。以下命令仅供调试。

**查看是否在运行：**
```powershell
Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like "*tts_watcher*" } | Select-Object ProcessId,CommandLine
```

**手动启动：**
```powershell
node tts_watcher.js
```

**手动停止：**
```powershell
Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like "*tts_watcher*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

---

## 配置参考

### 完整字段

```json
{
  "python": "python3",
  "voice": "zh-CN-XiaoyiNeural",
  "pollIntervalMs": 3000,
  "agentSessionDirs": [
    "~/.openclaw/agents/writer/sessions"
  ],
  "verbose": true
}
```

### 推荐语音

| 语音 | 风格 |
|------|------|
| `zh-CN-XiaoyiNeural` | 活泼轻快 **推荐** |
| `zh-CN-XiaoxiaoNeural` | 温暖标准 |
| `zh-CN-YunxiNeural` | 阳光男声 |
| `zh-CN-XiaochenNeural` | 冷静知性 |

列出所有中文女声：
```powershell
python edge_speak.py --list-voices
```

### 轮询间隔调优

| 值 | 响应速度 | 适合场景 |
|----|---------|---------|
| `6000` (6秒) | 较慢 | 省资源 |
| `3000` (3秒) | 正常 | 日常推荐 |
| `1500` (1.5秒) | 快 | 频繁对话 |
| `1000` (1秒) | 极速 | 需要秒打断 |

---

## 目录结构

```
claw-speak/
├── README.md              ← 本文件
├── SKILL.md               ← OpenClaw Skill 定义（需自行创建）
├── install.ps1            ← 一键安装脚本
├── config.example.json    ← 配置模板
├── config.json            ← 实际配置
├── tts_watcher.js         ← 核心：轮询监听器（v3，支持抢占中断）
├── edge_speak.py          ← 核心：Edge-TTS 封装（v3，纯内存处理）
└── output/                ← 不再使用，可删除
```

---

## 相关链接

- [Edge-TTS](https://github.com/rany2/edge-tts) — 微软 Edge TTS 引擎
- [OpenClaw](https://openclaw.ai) — AI Agent 框架
