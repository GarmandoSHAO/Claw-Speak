#!/usr/bin/env pwsh
<#
.SYNOPSIS
    claw-speak 一键安装脚本
.DESCRIPTION
    检查 Python 环境、安装 edge-tts + soundfile、复制配置文件、验证可运行。
    适用于 Windows + OpenClaw 环境。
#>

$ErrorActionPreference = "Stop"
$TOOLS_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$CONFIG_EXAMPLE = Join-Path $TOOLS_DIR "config.example.json"
$CONFIG_JSON = Join-Path $TOOLS_DIR "config.json"

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  claw-speak 一键安装" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ─── 第 1 步：检查 Python ──────────────────────────────
Write-Host "[第 1 步] 检查 Python 环境..." -ForegroundColor Yellow

$pythonCandidates = @(
    "python3",
    "python"
)

$pythonBin = $null
foreach ($cmd in $pythonCandidates) {
    try {
        $ver = & $cmd --version 2>$null
        if ($ver -match "Python 3\.(\d+)") {
            $minorVersion = [int]$Matches[1]
            if ($minorVersion -ge 10) {
                $pythonBin = (Get-Command $cmd).Source
                Write-Host "  ✓ 找到 Python 3: $pythonBin" -ForegroundColor Green
                Write-Host "    版本: $ver" -ForegroundColor DarkGray
                break
            }
        }
    } catch {}
}

# 尝试 conda 环境
if (-not $pythonBin) {
    $condaPaths = @(
        "$env:USERPROFILE\AppData\Local\anaconda3\envs\py312\python.exe",
        "$env:USERPROFILE\AppData\Local\miniconda3\envs\py312\python.exe",
        "D:\SCE\App\Anaconda\envs\py312\python.exe"
    )
    foreach ($p in $condaPaths) {
        if (Test-Path $p) {
            $pythonBin = $p
            Write-Host "  ✓ 找到 conda Python: $pythonBin" -ForegroundColor Green
            break
        }
    }
}

if (-not $pythonBin) {
    Write-Host "  ✗ 未找到 Python 3.10+，请先安装 Python" -ForegroundColor Red
    Write-Host "    下载: https://www.python.org/downloads/" -ForegroundColor DarkGray
    exit 1
}

# ─── 第 2 步：安装 Python 依赖 ─────────────────────────
Write-Host ""
Write-Host "[第 2 步] 安装 Python 依赖..." -ForegroundColor Yellow

$deps = @("edge-tts", "soundfile", "numpy")
foreach ($dep in $deps) {
    try {
        & $pythonBin -m pip install $dep -q
        Write-Host "  ✓ $dep 安装完成" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $dep 安装失败: $_" -ForegroundColor Red
    }
}

# ─── 第 3 步：创建配置文件 ──────────────────────────────
Write-Host ""
Write-Host "[第 3 步] 创建配置文件..." -ForegroundColor Yellow

if (Test-Path $CONFIG_JSON) {
    Write-Host "  ✓ config.json 已存在，跳过" -ForegroundColor DarkGray
} else {
    if (Test-Path $CONFIG_EXAMPLE) {
        Copy-Item $CONFIG_EXAMPLE $CONFIG_JSON
        Write-Host "  ✓ 已从 config.example.json 创建 config.json" -ForegroundColor Green
    }
}

# 写入正确的 python 路径到 config.json
try {
    $cfg = Get-Content $CONFIG_JSON -Raw | ConvertFrom-Json
    $cfg.python = $pythonBin
    $cfg | ConvertTo-Json | Set-Content $CONFIG_JSON -Encoding UTF8
    Write-Host "  ✓ Python 路径已写入 config.json" -ForegroundColor Green
} catch {
    Write-Host "  ! 写入 Python 路径失败（可手动编辑 config.json）" -ForegroundColor Yellow
}

# ─── 第 4 步：验证 edge_speak.py ───────────────────────
Write-Host ""
Write-Host "[第 4 步] 验证 TTS 引擎..." -ForegroundColor Yellow

try {
    $testText = "安装成功，moss TTS 纳米版已就绪"
    & $pythonBin (Join-Path $TOOLS_DIR "edge_speak.py") --text $testText
    Write-Host "  ✓ TTS 引擎验证通过" -ForegroundColor Green
} catch {
    Write-Host "  ! TTS 引擎验证失败: $_" -ForegroundColor Yellow
    Write-Host "    请检查网络连接（需要访问微软 Edge TTS 服务）" -ForegroundColor DarkGray
}

# ─── 完成 ───────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  claw-speak 安装完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "启动监听器：" -ForegroundColor White
Write-Host "  cd $TOOLS_DIR" -ForegroundColor DarkGray
Write-Host "  node tts_watcher.js" -ForegroundColor DarkGray
Write-Host ""
Write-Host "包装启动（带 Chat 联动）：" -ForegroundColor White
Write-Host "  $TOOLS_DIR\openclaw-chat.bat" -ForegroundColor DarkGray
Write-Host ""
Write-Host "查看可用语音：" -ForegroundColor White
Write-Host "  $pythonBin edge_speak.py --list-voices" -ForegroundColor DarkGray
Write-Host ""
Write-Host "停止：Ctrl+C" -ForegroundColor DarkGray
