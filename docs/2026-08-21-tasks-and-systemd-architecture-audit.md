# 🛠️ System Architecture & Code Audit: `/tasks`, achiAgy Commands & Crons

> **Date:** 2026-08-21  
> **Scope:** `achiAgy/src/bot.py`, `AIS-OS/tasks.md`, `AIS-OS/scripts/` (`daily_brief.py`, `tasks_digest.py`, `evening_debrief.py`, `vault_inbox_sync.py`, `service_failure_alert.py`), and `AIS-OS/systemd/` timers.  
> **Priority:** `!high` · **Assigned to:** Claude Code

---

## 🎯 Executive Summary & Root Cause

The `/tasks` command returned stale/finished tasks because it was never implemented as a deterministic Python command. Instead, `bot.py` forwarded `"/tasks"` directly to the LLM agent pipeline, which executed exploratory filesystem searches and grepped across historical session logs in `tgdb/`.

Additionally, the audit identified:
1. **Triplicated Task Parsers:** `daily_brief.py`, `tasks_digest.py`, and `evening_debrief.py` maintain separate, diverging regex implementations.
2. **Concurrency & Orphan Tasks:** `active_tasks[chat_id]` gets overwritten without canceling running tasks, causing resource leaks.
3. **Security Gap in Git Sync:** `vault_inbox_sync.py` commits mobile inbox captures without running secret/token sanitization.
4. **Failure Alert Reliability:** `service_failure_alert.py` lacks a persistent retry queue for network outages.

---

## 🔍 Detailed Audit Findings

### 1. The `/tasks` Command Discrepancy & Parser Architecture
* **Location:** [`achiAgy/src/bot.py:968-975`](file:///home/achibukz/Code/GitHub/achiAgy/src/bot.py#L968-L975)
* **Problem:** 
  ```python
  async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
      task = asyncio.create_task(execute_agent_pipeline(update, "/tasks"))
      active_tasks[chat_id] = task
  ```
  This treats `/tasks` as an open-ended LLM prompt. The agent burns 5–15 seconds and hundreds of tokens, often searching `tgdb/` session history and hallucinating completed tasks.
* **Fix:** Convert `cmd_tasks` into a native deterministic Python handler that reads `tasks.md`, parses `## Active`, formats clean checkboxes, and replies in <50ms with 0 token overhead.

### 2. Duplicated Regex & Parsing Across AIS-OS Scripts
* **Locations:**
  - [`AIS-OS/scripts/daily_brief.py:40-108`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/daily_brief.py#L40-L108)
  - [`AIS-OS/scripts/tasks_digest.py:34-109`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/tasks_digest.py#L34-L109)
  - [`AIS-OS/scripts/evening_debrief.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/evening_debrief.py)
* **Problem:** Each script duplicates `TASK_RE`, `DUE_RE`, `PRIORITY_RE`, `AREA_RE`, `FENCE_RE`, `LINK_RE`, `strip_markup`, and `parse_active_tasks`.
* **Discrepancy Example:** `tasks_digest.py` includes `MD_LINK_RE` to strip markdown links (`[Label](url)`), but `daily_brief.py` is missing it, causing markdown syntax to leak into the morning brief.
* **Fix:** Extract shared parsing logic into `AIS-OS/scripts/task_engine.py` with unified dataclasses, link sanitization, and state handling.

### 3. Telegram Bot Concurrency & Task Cancellation
* **Location:** [`achiAgy/src/bot.py:975, 986, 995`](file:///home/achibukz/Code/GitHub/achiAgy/src/bot.py#L975)
* **Problem:** Overwriting `active_tasks[chat_id] = task` without checking if an earlier task is still running leaves orphan background processes running indefinitely.
* **Fix:** Check `if chat_id in active_tasks and not active_tasks[chat_id].done():` and explicitly `cancel()` the previous task or reject concurrent execution with a status notice.

### 4. Git Vault Sync Secret Sanitization
* **Location:** [`AIS-OS/scripts/vault_inbox_sync.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/vault_inbox_sync.py)
* **Problem:** Automatically stages, commits, and pushes `achiMem/inbox/` and `schoolMem/inbox/` without running regex token/secret redactions (unlike `tgdb_logger.py`).
* **Fix:** Run regex secret scanning/sanitization on staged inbox markdown files prior to `git commit`.

### 5. Failure Alert Store-and-Forward Channel
* **Location:** [`AIS-OS/scripts/service_failure_alert.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/service_failure_alert.py)
* **Problem:** Alerts sent during a DNS or network drop fail silently.
* **Fix:** Buffer unsent alerts to `~/.local/state/achios/failed_alerts.json` and retry on the next timer trigger.

---

## 📋 Implementation Checklist for Claude Code

- [ ] **1. Shared Task Engine:** Create `AIS-OS/scripts/task_engine.py` housing `Task` dataclass, unified regexes (`MD_LINK_RE`, `LINK_RE`, `BOLD_RE`, `CODE_RE`), and `parse_tasks(content: str, section: str = 'active')`.
- [ ] **2. Refactor AIS-OS Scripts:** Update `daily_brief.py`, `tasks_digest.py`, and `evening_debrief.py` to import from `task_engine.py`.
- [ ] **3. Native `/tasks` Handler in achiAgy:** Replace LLM forwarding in `cmd_tasks()` in `achiAgy/src/bot.py` with native `task_engine` reading and Telegram formatting.
- [ ] **4. Concurrency Guard in achiAgy:** Implement `active_tasks` cancellation guard in `execute_agent_pipeline` / `handle_text_message`.
- [ ] **5. Vault Sync Sanitizer:** Add secret/token redaction filter to `vault_inbox_sync.py` before git commits.
