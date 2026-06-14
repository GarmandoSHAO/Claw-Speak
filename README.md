# claw-speak v3

**OpenClaw Skill** — Auto-speak AI replies aloud via Microsoft Edge-TTS.

---

## Installation

### Step 1: Install the Skill

```powershell
# Install to current workspace (default)
openclaw skills install git:GarmandoSHAO/Claw-Speak

# Or install globally (available to all agents)
openclaw skills install git:GarmandoSHAO/Claw-Speak --global
```

### Step 2: Install Python Dependencies

```powershell
pip install edge-tts soundfile numpy
```

### Step 3: Configure

Locate `config.json` after installation:

- Workspace install: `~/.openclaw/workspace/skills/claw-speak/config.json`
- Global install: under OpenClaw's global skills directory

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

`agentSessionDirs` — list the agents you want to monitor.

List your agents:
```powershell
dir ~/.openclaw/agents/*/sessions/
```

### Step 4: Configure Your Agent

Add this to your agent's `SOUL.md`:

```
**Auto TTS Listener**: Before each reply, check if the TTS watcher is running.
Check method: Get-CimInstance to query node.exe process for "tts_watcher" in command line.
If not running, start with: Start-Process -WindowStyle Hidden tts_watcher.js
```

### Step 5: Verify

Send a message to your agent. You should hear the reply spoken aloud within a few seconds.

---

## Features

| Feature | Description |
|---------|-------------|
| **Preemptive Interrupt** | New message stops current TTS mid-play and starts reading the latest |
| **Multi-Agent** | Single watcher monitors multiple agents at once |
| **In-Memory Audio** | Audio processed entirely in RAM — no disk writes |
| **Direct Microsoft TTS** | No proxy needed |
| **Zero UI** | Pure command-line background process, no windows |

---

## Available Voices

```powershell
python edge_speak.py --list-voices
```

Common Chinese voices:

| Voice | Style |
|-------|-------|
| `zh-CN-XiaoyiNeural` | Cheerful **Recommended** |
| `zh-CN-XiaoxiaoNeural` | Warm standard |
| `zh-CN-YunxiNeural` | Sunny male |
| `zh-CN-XiaochenNeural` | Calm intellectual |
| `zh-CN-liaoning-XiaobeiNeural` | Humorous (Northeastern dialect) |
| `zh-CN-shaanxi-XiaoniNeural` | Bright (Shaanxi dialect) |

Common English voices:

| Voice | Style |
|-------|-------|
| `en-US-AriaNeural` | Friendly female **Recommended** |
| `en-US-JennyNeural` | Warm female |
| `en-US-GuyNeural` | Calm male |
| `en-US-TonyNeural` | Deep male |
| `en-GB-SoniaNeural` | British female |
| `en-GB-RyanNeural` | British male |

---

## Useful Commands

**Check if the watcher is running:**
```powershell
Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like "*tts_watcher*" } | Select-Object ProcessId,CommandLine
```

**Start manually:**
```powershell
cd <claw-speak install directory>
node tts_watcher.js
```

**Stop manually:**
```powershell
Stop-Process -Id <PID> -Force
```

---

## Directory Structure

```
claw-speak/
├── SKILL.md            ← Skill definition
├── README.md           ← This file (English)
├── README_zh.md        ← 中文说明
├── install.ps1         ← Install script
├── config.json         ← Configuration
├── config.example.json ← Config template
├── tts_watcher.js      ← Polling watcher
└── edge_speak.py       ← Edge-TTS wrapper
```
