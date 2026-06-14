#!/usr/bin/env node
/**
 * TTS 自动朗读监听器
 *
 * 监听 OpenClaw agent session 文件，有新 assistant 回复时自动调用 TTS 朗读。
 *
 * 启动：node tts_watcher.js
 * 停止：Ctrl+C
 *
 * 配置：同目录下 config.json 可覆盖默认值（参见 config.example.json）
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const execFileAsync = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── 默认配置 ──────────────────────────────────────────
const DEFAULTS = {
  python: "python3",
  voice: "zh-CN-XiaoyiNeural",
  pollIntervalMs: 6000,
  agentSessionDirs: [join(homedir(), ".openclaw", "agents", "writer", "sessions")],
  proxy: "http://127.0.0.1:7890",
  verbose: true,
};

let CONFIG = { ...DEFAULTS };

// ─── 加载用户配置 ───────────────────────────────────────
function loadConfig() {
  try {
    const cfgPath = join(__dirname, "config.json");
    const raw = readFileSync(cfgPath, "utf-8");
    const userCfg = JSON.parse(raw);
    CONFIG = { ...DEFAULTS, ...userCfg };
  } catch {
    // config.json 不存在就使用默认值
  }
}

loadConfig();

const TTS_SCRIPT = join(__dirname, "edge_speak.py");
let lastAssistantText = "";

// ─── Session 文件查找 ───────────────────────────────────

/** 在多个 session 目录中找到最新的 .jsonl 文件 */
function findLatestJsonl() {
  let latest = null;
  let latestMtime = 0;

  for (const dir of CONFIG.agentSessionDirs) {
    try {
      const files = readdirSync(dir)
        .filter((f) => f.endsWith(".jsonl") && !f.includes("trajectory"));

      for (const f of files) {
        const fp = join(dir, f);
        const mtime = statSync(fp).mtimeMs;
        if (mtime > latestMtime) {
          latest = fp;
          latestMtime = mtime;
        }
      }
    } catch {
      // 目录不存在则跳过
    }
  }

  return latest;
}

// ─── 提取回复文本 ──────────────────────────────────────

/** 从 .jsonl 文件中提取最后一条 assistant 回复的纯文本 */
function getLastAssistantReply(filePath) {
  try {
    const content = readFileSync(filePath, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);
    if (lines.length === 0) return null;

    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const entry = JSON.parse(lines[i]);
        if (entry.type !== "message") continue;

        const msg = entry.message;
        if (!msg || msg.role !== "assistant") continue;

        const rawContent = msg.content;
        if (!rawContent) continue;

        let text = "";

        if (typeof rawContent === "string") {
          text = rawContent;
        } else if (Array.isArray(rawContent)) {
          text = rawContent
            .filter((block) => block.type === "text")
            .map((block) => block.text)
            .join("")
            .trim();
        }

        if (text && text.length > 5) return text;
      } catch {
        continue;
      }
    }
    return null;
  } catch {
    return null;
  }
}

// ─── 文本清理 ──────────────────────────────────────────

/** 清理 Markdown 标记，提取纯文本给 TTS 朗读 */
function stripMarkdown(text) {
  return text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`[^`]+`/g, "")
    .replace(/^#+\s*/gm, "")
    .replace(/\*\*/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^-{3,}/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

// ─── 核心轮询 ──────────────────────────────────────────

async function checkForNewReply() {
  const file = findLatestJsonl();
  if (!file) return;

  const reply = getLastAssistantReply(file);
  if (!reply) return;

  if (reply === lastAssistantText) return;

  if (!lastAssistantText) {
    lastAssistantText = reply;
    return;
  }

  lastAssistantText = reply;

  const cleanText = stripMarkdown(reply);
  if (!cleanText || cleanText.length < 5) {
    if (CONFIG.verbose) console.log("[tts-watcher] 清理后文本太短，跳过朗读");
    return;
  }

  if (CONFIG.verbose) {
    console.log(`[tts-watcher] 新回复 (${reply.length} 字)：${cleanText.slice(0, 60)}...`);
  }

  try {
    await execFileAsync(CONFIG.python, [
      TTS_SCRIPT,
      "--text",
      cleanText,
      "--voice",
      CONFIG.voice,
    ]);
    if (CONFIG.verbose) console.log("[tts-watcher] 朗读完成");
  } catch (err) {
    console.error("[tts-watcher] 朗读失败:", err.message);
  }
}

// ─── 启动 ──────────────────────────────────────────────

console.log("═══════════════════════════════════════════");
console.log("  claw-speak - TTS 自动朗读监听器");
console.log(`  监听目录: ${CONFIG.agentSessionDirs.join(", ")}`);
console.log(`  轮询间隔: ${CONFIG.pollIntervalMs}ms`);
console.log(`  语音: ${CONFIG.voice}`);
console.log("  Ctrl+C 停止");
console.log("═══════════════════════════════════════════");

// 首次只记录不朗读，启动后先跳过历史
checkForNewReply();
setInterval(checkForNewReply, CONFIG.pollIntervalMs);
