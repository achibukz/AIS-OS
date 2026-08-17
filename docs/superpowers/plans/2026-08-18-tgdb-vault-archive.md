# Universal Telegram Database (tgdb) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-optimized:subagent-driven-development` or `superpowers-optimized:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize and archive all conversations across the 4 Telegram bots (`@achiOSClaudeBot`, `@schoMemBot`, `@achiAgyBot`, `@schoMemAGYBot`) into `achiMem/tgdb/` as structured, searchable Markdown notes with automated secret sanitization, cross-bot recall, and 15-minute GitHub vault synchronization.

**Architecture:** 
A shared Python logging/export module (`scripts/tgdb_logger.py`) hooks into the message lifecycle of all bots. Transcripts are buffered per session, sanitized of secrets, formatted with YAML frontmatter + executive takeaways + collapsible full dialog, and written to `achiMem/tgdb/YYYY-MM/YYYY-MM-DD-<bot>-<session>.md`. The existing `vault_inbox_sync.py` daemon is expanded to watch and sync `achiMem/tgdb/` alongside `inbox/`.

**Tech Stack:** Python 3, Systemd user timers, Git autostash rebase, Obsidian Markdown / Dataview schema.

**Assumptions:**
- Assumes `achiMem` is a cloned git repository at `/home/achibukz/Documents/Obsidian/achiMem` tracking `origin/main`.
- Assumes bot sessions generate identifiable session identifiers and complete turn cycles.

---

## 1. Directory Structure & Note Schema

### File Placement:
```
achiMem/
└── tgdb/
    └── YYYY-MM/
        └── YYYY-MM-DD-<bot>-<session_id>.md
```

### Note Structure:
```markdown
---
title: "<Session Title / Topic Gist>"
bot: "@<bot_username>"
engine: "<Claude Sonnet | Gemini Pro/Flash>"
channel: "Telegram DM"
date: YYYY-MM-DD HH:MM
tags: [tgdb, session, <domain_tags>]
summary: "<1-2 sentence executive summary>"
---

# 💬 <Session Title>
* **Bot:** `@<bot_username>` (<Engine>)
* **Date:** <Formatted Date> Manila
* **Summary:** <Summary text>

---

### 📌 Key Takeaways & Decisions
* <Bulleted takeaway or decision>

### ⚡ Extracted Action Items
- [ ] <Action item if surfaced>

---

### 📜 Full Dialogue Transcript
<details open>
<summary><b>Expand / Collapse Transcript</b></summary>

> **Aki:** <User prompt>
>
> **@<bot_username>:** <Assistant response>

</details>
```

---

## 2. The 5 Core Safeguards

1. **Anti-Bloat & Performance:** Session bundling (1 note per session/topic, not per message) + monthly folder partitioning (`tgdb/YYYY-MM/`).
2. **Anti-Leak Secret Redaction:** Strict regex sanitization on all text before disk write (redacting `sk-ant-*`, `AIzaSy*`, `bot[0-9]+:...`, tokens, API keys, passwords).
3. **Anti-Collision File Isolation:** Filenames prefixed with bot name and session ID (`YYYY-MM-DD-<bot>-<session_id>.md`), ensuring multiple bots writing at the same time never collide.
4. **Anti-Fragment Flushed Writes:** Writes/updates are atomic on turn completion (`on_turn_end` / `on_session_idle`).
5. **Git Sync Resilience:** `scripts/vault_inbox_sync.py` watches `achiMem/tgdb` with `git pull --rebase --autostash` and stale lock clearing.

---

## 3. Implementation Tasks

### Task 1: Create Shared tgdb Logger & Secret Redactor
**Files:**
- Create: `scripts/tgdb_logger.py`
- Test: `tests/test_tgdb_logger.py`

**Security flag:** `security` (Handles secret redaction patterns and safe Markdown writing).

- [ ] Implement `sanitize_secrets(text: str) -> str` using comprehensive regex rules for tokens/keys.
- [ ] Implement `format_tgdb_note(metadata: dict, messages: list[dict], takeaways: list[str], tasks: list[str]) -> str`.
- [ ] Implement `write_tgdb_session(vault_path: Path, bot_name: str, session_id: str, content: str) -> Path`.
- [ ] Write unit tests verifying secret redaction, folder creation, and file formatting.

**Verification command:**
```bash
/home/achibukz/.local/share/achios/venv/bin/python -m pytest tests/test_tgdb_logger.py
```
**Expected outcome:** All tests pass with 100% secret redaction verification.

---

### Task 2: Expand Vault Inbox Sync to Watch `achiMem/tgdb`
**Files:**
- Modify: `scripts/vault_inbox_sync.py`

**Security flag:** `none`

- [ ] Add `tgdb` to the `watch_dirs` list for `achiMem` in `VAULTS` configuration:
  ```python
  {
      "name": "achiMem",
      "path": Path.home() / "Documents" / "Obsidian" / "achiMem",
      "branch": "main",
      "watch_dirs": ["inbox", "tgdb"],
  }
  ```
- [ ] Add automatic stale `.git/index.lock` detection (>5 mins old removal) before git operations.
- [ ] Test `--dry-run` to verify `achiMem/tgdb` detection.

**Verification command:**
```bash
/home/achibukz/.local/share/achios/venv/bin/python scripts/vault_inbox_sync.py --dry-run
```
**Expected outcome:** Reports `achiMem` clean and ready to watch `tgdb`.

---

### Task 3: Wire Transcript Logging into `achiAgy` Bots
**Files:**
- Modify: `/home/achibukz/Code/GitHub/achiAgy/src/telegram_bot.py` or `/home/achibukz/Code/GitHub/achiAgy/src/session_manager.py`

**Security flag:** `none`

- [ ] Hook `on_response_complete` in `achiAgy` (`@achiAgyBot` and `@schoMemAGYBot`).
- [ ] Format session messages and invoke `tgdb_logger.write_tgdb_session()`.
- [ ] Test sending a test message to `@achiAgyBot` and verify the created note in `achiMem/tgdb/2026-08/`.

**Verification command:**
```bash
ls -la /home/achibukz/Documents/Obsidian/achiMem/tgdb/2026-08/
```
**Expected outcome:** Generated `.md` file with proper YAML frontmatter and transcript.

---

### Task 4: Wire Transcript Logging into Claude Code Bots
**Files:**
- Modify: `scripts/telegram-bot.sh` / `scripts/run-bot.sh` / Claude hook transcript export

**Security flag:** `none`

- [ ] Add session end hook / transcript capture for `@achiOSClaudeBot` and `@schoMemBot`.
- [ ] Test with a short prompt and verify transcript landing in `achiMem/tgdb/2026-08/`.

**Verification command:**
```bash
ls -la /home/achibukz/Documents/Obsidian/achiMem/tgdb/2026-08/
```
**Expected outcome:** Clean `.md` transcript generated for Claude Code sessions.

---

### Task 5: End-to-End Vault Sync & Verification
**Files:**
- Modify: `tasks.md`, `session-log.md`, `AGENTS.md`

**Security flag:** `none`

- [ ] Trigger real sync: `systemctl --user start achios-vault-sync.service`.
- [ ] Verify commit and push on `https://github.com/achibukz/achiMem.git`.
- [ ] Document in `AGENTS.md` and `session-log.md`.

**Verification command:**
```bash
cd /home/achibukz/Documents/Obsidian/achiMem && git log -n 2
```
**Expected outcome:** Clean git log showing synced `tgdb` archives.
