# claw-speak v3

**OpenClaw Skill** —— AI 回复后自动用微软 Edge-TTS 读出声音来。

---

## 安装

### 第一步：安装 Skill

```powershell
# 安装到当前工作区（默认）
openclaw skills install git:GarmandoSHAO/Claw-Speak

# 或安装到全局（所有 agent 可用）
openclaw skills install git:GarmandoSHAO/Claw-Speak --global
```

### 第二步：安装 Python 依赖

```powershell
pip install edge-tts soundfile numpy
```

### 第三步：修改配置

安装后找到 `config.json`：

- 工作区安装：`~/.openclaw/workspace/skills/claw-speak/config.json`
- 全局安装：OpenClaw 的全局 skill 目录下

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

`agentSessionDirs` 列出你想监听哪些 agent 的回复。

查看你的 agent 有哪些：
```powershell
dir ~/.openclaw/agents/*/sessions/
```

### 第四步：配置 Agent

在你的 Agent 的 `SOUL.md` 中添加以下指令：

```
**自动朗读监听**：每次回复前，检查 TTS 监听器是否运行。
检查方法：Get-CimInstance 查询 node.exe 进程命令行中是否包含 tts_watcher。
如未运行，用 Start-Process -WindowStyle Hidden 启动 tts_watcher.js。
```

### 第五步：验证

给你的 agent 发一条消息。回复后几秒内应听到扬声器出声。

---

## 特性

| 特性 | 说明 |
|------|------|
| **抢占式中断** | 快速连发消息时，自动中断上一条朗读，直接读最新的 |
| **多 Agent** | 一个监听器同时监听多个 agent |
| **纯内存处理** | 音频全程在内存中转换，不写磁盘 |
| **直连微软 TTS** | 不需要梯子 |
| **零窗口干扰** | 纯命令行后台运行，不弹窗口 |

---

## 查看可用语音

```powershell
python edge_speak.py --list-voices
```

常用中文语音：

| 语音 | 风格 |
|------|------|
| `zh-CN-XiaoyiNeural` | 活泼轻快 **推荐** |
| `zh-CN-XiaoxiaoNeural` | 温暖标准 |
| `zh-CN-YunxiNeural` | 阳光男声 |
| `zh-CN-XiaochenNeural` | 冷静知性 |
| `zh-CN-liaoning-XiaobeiNeural` | 幽默东北话 |
| `zh-CN-shaanxi-XiaoniNeural` | 明亮陕西话 |

---

## 相关命令

**查看监听器运行状态：**
```powershell
Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like "*tts_watcher*" } | Select-Object ProcessId,CommandLine
```

**手动启动：**
```powershell
cd <claw-speak 安装目录>
node tts_watcher.js
```

**手动停止：**
```powershell
Stop-Process -Id <PID> -Force
```

---

## 目录结构

```
claw-speak/
├── SKILL.md            ← 技能定义
├── README.md           ← 本文件
├── install.ps1         ← 安装脚本
├── config.json         ← 配置
├── config.example.json ← 配置模板
├── tts_watcher.js      ← 轮询监听器
└── edge_speak.py       ← Edge-TTS 封装
```
