# claw-speak v3

**OpenClaw Skill** —— AI 回复后自动用微软 Edge-TTS 读出声音来。

---

## 部署步骤

### 第一步：获取文件

```powershell
git clone <仓库地址> ~/.openclaw/tools/claw-speak/
```

### 第二步：检查依赖

| 依赖 | 最低版本 | 用途 |
|------|---------|------|
| **Node.js** | v18+ | 运行 tts_watcher 监听器 |
| **Python** | 3.10+ | 运行语音合成 |

```powershell
node --version
python --version
```

### 第三步：安装 Python 包

```powershell
pip install edge-tts soundfile numpy
```

### 第四步：修改配置

打开 `config.json`，填写实际信息。

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

### 第五步：配置 Agent

在你的 Agent 的 `SOUL.md` 中添加以下指令：

```
**自动朗读监听**：每次回复前，检查 TTS 监听器是否运行。
检查方法：Get-CimInstance 查询 node.exe 进程命令行中是否包含 tts_watcher。
如未运行，用 Start-Process -WindowStyle Hidden 启动 tts_watcher.js。
```

### 第六步：验证

给你的 agent 发一条消息。回复后几秒内应听到扬声器出声。

---

## 特性

| 特性 | 说明 |
|------|------|
| **抢占式中断** | 快速连发消息时，自动中断上一条朗读，直接读最新的 |
| **多 Agent** | 一个监听器同时监听多个 agent |
| **纯内存处理** | 音频全程在内存中转换，不写磁盘 |
| **直连微软 TTS** | 不需要梯子 |
| **零窗口干扰** | 纯命令行后台运行 |

---

## 相关命令

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

## 目录结构

```
claw-speak/
├── README.md            ← 本文件
├── config.example.json  ← 配置模板
├── config.json          ← 实际配置
├── tts_watcher.js       ← 轮询监听器
├── edge_speak.py        ← Edge-TTS 封装
└── install.ps1          ← 安装脚本
