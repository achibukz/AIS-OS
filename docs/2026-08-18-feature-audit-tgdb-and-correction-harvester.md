# 🔍 Feature Audit & Verification Brief for Claude Code

* **Date:** August 18, 2026
* **Target Reviewer:** Claude Code (`@achiOSClaudeBot` / Sonnet)
* **Branch Under Review:** `feat/correction-harvester`
* **Parent Branch:** `main`
* **Status:** Ready for Audit (Do Not Merge Yet)

---

## 🎯 Executive Summary & Purpose

This audit document provides a complete technical specification, architectural flow, test commands, and verification checklist for Claude Code to audit two newly built achiOS capabilities:

1. **Universal TGDB Vault Archive & Exporter** (`scripts/export_transcripts.py`, `scripts/tgdb_logger.py`)
2. **Autonomous Correction Harvester & Self-Learning Loop** (`scripts/extract_corrections.py`, `scripts/vault_inbox_sync.py`, `scripts/evening_debrief.py`)

---

## 📦 Feature 1: Universal TGDB Vault Archive & Exporter

### 1. Purpose & Core Responsibilities
Automatically preserves raw dialogue sessions from **both Claude Code and Antigravity (Gemini)** into clean, human-readable, sanitized Markdown notes inside Obsidian (`achiMem/tgdb/YYYY-MM/`).

### 2. Architecture & File Registry
* **Core Logger:** [`scripts/tgdb_logger.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/tgdb_logger.py)
  * Formats frontmatter metadata, extracted action items (`- [ ]`), decision takeaways, and collapsible dialogue transcripts.
* **Universal Exporter:** [`scripts/export_transcripts.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/export_transcripts.py)
  * Sweeps `~/.claude/projects/` (Claude Code JSONL sessions).
  * Sweeps `~/.gemini/antigravity-cli/brain/` (Antigravity `transcript.jsonl` logs).
  * Detects bot handles:
    * Claude Code: `@achiOSClaudeBot` (or `@schoMemBot` if in schoolMem cwd).
    * Antigravity CLI: `@achiAgyOSBot` (or `@schoMemAGYBot` if in schoolMem cwd).
  * Detects active AI engine (`Claude Sonnet` vs `Gemini 3.7 Flash`).
* **Vault Destination:** `~/Documents/Obsidian/achiMem/tgdb/YYYY-MM/YYYY-MM-DD-<bot>-<hash>.md`

### 3. Sanitization & Redaction Guarantees
* Strips all sensitive credentials (`sk-ant-*`, `AIzaSy*`, Telegram bot tokens, bearer secrets).
* Strips noisy intermediate tool execution dumps (e.g. raw shell dumps, internal subagent stop tags, `<command-args>`, `<persisted-output>`, `<thought>` tags).
* Preserves user intent, user corrections, and final assistant replies.

### 4. Claude Code Audit Checklist for Feature 1
- [ ] Inspect [`scripts/export_transcripts.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/export_transcripts.py) lines 58–106 (`clean_claude_text` and `clean_antigravity_text`) for any potential edge-case XML tag leakage.
- [ ] Verify that bot handle detection accurately distinguishes between `@achiOSClaudeBot` and `@achiAgyOSBot`.
- [ ] Verify monthly partitioning logic (`YYYY-MM`) and timezone conversions (`Asia/Manila`).
- [ ] Run unit tests:
  ```bash
  PYTHONPATH=scripts pytest tests/test_export_transcripts.py tests/test_tgdb_logger.py
  ```

---

## ⚙️ Feature 2: Autonomous Correction Harvester & Self-Learning Loop

### 1. Purpose & Core Responsibilities
Transforms real-time user feedback, tone adjustments, directives, and banned words given in Telegram chat into persistent, deduplicated rules inside [`.agentrules`](file:///home/achibukz/Code/GitHub/AIS-OS/.agentrules) and [`decisions/log.md`](file:///home/achibukz/Code/GitHub/AIS-OS/decisions/log.md).

### 2. Architecture & File Registry
* **Harvester Engine:** [`scripts/extract_corrections.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/extract_corrections.py)
  * Scans recent tgdb Markdown files for user correction patterns.
  * **Heuristic Triggers:**
    1. *Banned words / terms:* `"don't use the word X"`, `"never use Y"`, `"stop saying Z"` (excludes CLI commands like `curl`, `git`, `python`).
    2. *Tone / style adjustments:* `"less formal"`, `"more casual"`, `"too formal"`.
    3. *Directives & rules:* `"take note that..."`, `"make sure to..."`, `"remember that..."`.
    4. *Formatting overrides:* `"change X to Y"` (excludes questions like `"how to change X?"`).
  * **Domain Classification:** Automatically routes rules into `voice`, `tasks`, `logging`, `infra`, or `general`.
* **Zero-Duplicate Engine:** Compares normalized candidate strings against `.agentrules`, `references/voice.md`, and `decisions/log.md` before applying.
* **Continuous Sync Pipeline:** [`scripts/vault_inbox_sync.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/vault_inbox_sync.py)
  * Runs every 15 minutes via `achios-vault-sync.timer`.
  * Exports transcripts and immediately executes `extract_corrections.py` so corrections take effect within 15 minutes.
* **Two-Message Evening Debrief Integration:** [`scripts/evening_debrief.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/evening_debrief.py)
  * Message 1: Daily accomplishments, service health, tomorrow's focus.
  * Message 2: Standalone `🧠 Self-Learning & Harvested Rules` message sent right after Message 1.

### 3. Claude Code Audit Checklist for Feature 2
- [ ] Inspect [`scripts/extract_corrections.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/extract_corrections.py) lines 70–170 for regex robustness and false-positive prevention.
- [ ] Verify `is_rule_duplicate()` logic to ensure duplicate phrases or previously logged banned words cannot be re-appended.
- [ ] Verify that `scripts/evening_debrief.py` correctly handles days with zero harvested rules (omits Message 2 cleanly without error).
- [ ] Run unit tests:
  ```bash
  PYTHONPATH=scripts pytest tests/test_extract_corrections.py tests/test_evening_debrief.py
  ```

---

## 🧪 Verification & Drill Runbook

Execute the following commands in order to verify full functionality:

```bash
# 1. Ensure working directory is AIS-OS on feat/correction-harvester
cd ~/Code/GitHub/AIS-OS
git status

# 2. Run the full pytest test suite
PYTHONPATH=scripts ~/.local/share/achios/venv/bin/pytest \
    tests/test_extract_corrections.py \
    tests/test_export_transcripts.py \
    tests/test_tgdb_logger.py \
    tests/test_evening_debrief.py \
    tests/test_telegram_notify.py

# 3. Test correction harvester dry-run on recent vault notes
PYTHONPATH=scripts ~/.local/share/achios/venv/bin/python \
    scripts/extract_corrections.py --dry-run --days 2

# 4. Test two-message evening debrief dry-run
PYTHONPATH=scripts ~/.local/share/achios/venv/bin/python \
    scripts/evening_debrief.py --dry-run
```

---

## 📂 Modified & Created Files on `feat/correction-harvester`

| File | Status | Description |
| :--- | :--- | :--- |
| [`scripts/extract_corrections.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/extract_corrections.py) | **New** | Autonomous Correction Harvester core script |
| [`tests/test_extract_corrections.py`](file:///home/achibukz/Code/GitHub/AIS-OS/tests/test_extract_corrections.py) | **New** | Unit test suite for correction extraction & deduplication |
| [`tests/test_evening_debrief.py`](file:///home/achibukz/Code/GitHub/AIS-OS/tests/test_evening_debrief.py) | **New** | Unit test suite for two-message debrief layout |
| [`scripts/export_transcripts.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/export_transcripts.py) | Modified | Updated bot handle to `@achiAgyOSBot` and dynamic Gemini model detection |
| [`scripts/vault_inbox_sync.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/vault_inbox_sync.py) | Modified | Integrated continuous 15-minute harvesting step |
| [`scripts/evening_debrief.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/evening_debrief.py) | Modified | Added standalone Message 2 for Self-Learning & Harvested Rules |
| [`AGENTS.md`](file:///home/achibukz/Code/GitHub/AIS-OS/AGENTS.md) | Modified | Added documentation for Correction Harvester |
| [`tasks.md`](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) | Modified | Moved harvester task to Done |
| [`.agentrules`](file:///home/achibukz/Code/GitHub/AIS-OS/.agentrules) | Modified | Added Section 5 for harvested rules |
| [`decisions/log.md`](file:///home/achibukz/Code/GitHub/AIS-OS/decisions/log.md) | Modified | Appended provenance decision logs for harvested corrections |

---
