# Comprehensive System Architecture & Session Audit
**Target Audience:** Claude Opus (Deep Audit & Architecture Review)  
**Audit Target Date:** 2026-08-20 23:00 (Post-Quota Reset)  
**Author / Orchestrator:** Antigravity (Gemini 3.7 Flash) & achiOS  
**Scope:** Everything designed, built, and operationalized across the `achibuntu` server, `AIS-OS`, `achiAgy`, `achiMem`, and `schoolMem` since the inception of the Telegram bot ecosystem (Aug 16–19, 2026).

---

## Executive Summary

Between August 16 and August 19, 2026, the `achibuntu` headless laptop server was transformed into an autonomous, multi-agent AI operating hub. This document serves as the master manifest of all running units, scripts, architectural contracts, data pipelines, and known operational quirks to be audited by **Claude Opus**.

```
                           ┌─────────────────────────────────────────────────────────────┐
                           │                    TELEGRAM CLIENTS                         │
                           │  @achiOSBot  •  @achiAgyOSBot  •  @schoMemBot  •  @achiETFBot│
                           └──────────────────────────────┬──────────────────────────────┘
                                                          │
                                         ┌────────────────┴────────────────┐
                                         │                                 │
                         ┌───────────────▼────────────────┐ ┌──────────────▼───────────────┐
                         │   achiOS / Scheduled Daemons    │ │    achiAgy Telegram Daemon      │
                         │ (Systemd Timers + Python Crons)│ │ (TUI + Session Mgr + AGY CLI) │
                         └───────────────┬────────────────┘ └──────────────┬───────────────┘
                                         │                                 │
                 ┌───────────────────────┼─────────────────────────────────┼───────────────────────┐
                 │                       │                                 │                       │
      ┌──────────▼──────────┐ ┌──────────▼──────────┐           ┌──────────▼──────────┐ ┌──────────▼──────────┐
      │   TGDB Archiver     │ │ Correction Harvester│           │ Vault Auto-Sync     │ │  Hermes Gateway &   │
      │ (Universal Session  │ │ (Feedback Analyzer  │           │ (15-min Git Auto-   │ │ Google Workspace    │
      │  Transcripts)       │ │  & Rule Synthesizer)│           │  Stash Rebase Sync) │ │ (Calendar + Gmail)  │
      └──────────┬──────────┘ └──────────┬──────────┘           └──────────┬──────────┘ └─────────────────────┘
                 │                       │                                 │
                 └───────────────────────┴────────────────┬────────────────┘
                                                          │
                                            ┌─────────────▼─────────────┐
                                            │      OBSIDIAN VAULTS      │
                                            │   achiMem  •  schoolMem   │
                                            └───────────────────────────┘
```

---

## 1. Systemd Timers & Scheduled Crons (`AIS-OS/systemd/` & `scripts/`)

All background operations run as systemd user services (`systemctl --user`) backed by `.timer` units. Every service has `OnFailure=achios-failure-alert@%n.service` attached for immediate crash alerting.

| Unit Name | Timer / Schedule | Python Script | Purpose & Delivery Channel | Relevant Files |
|---|---|---|---|---|
| **`achios-daily-brief`** | `08:00 AM` Daily | `scripts/daily_brief.py` | Google Calendar schedule + Top 5 priority tasks from `tasks.md` → `@achiOSBot` | [`systemd/achios-daily-brief.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-daily-brief.timer), [`scripts/daily_brief.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/daily_brief.py) |
| **`achios-tasks-digest`**| `11am, 3pm, 6pm, 9pm, 11pm` | `scripts/tasks_digest.py` | High-priority task checkpoint reminders → `@achiOSBot` | [`systemd/achios-tasks-digest.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-tasks-digest.timer), [`scripts/tasks_digest.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/tasks_digest.py) |
| **`achios-voo-digest`**  | `04:30 AM` & `08:00 AM` (Daily) | `scripts/voo_digest.py` | US Market close review for VOO, VXUS, QQQM → `@achiETFBot` / `@achiOSBot` | [`systemd/achios-voo-digest.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-voo-digest.timer), [`scripts/voo_digest.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/voo_digest.py) |
| **`achios-etf-weekly`**  | `Sun 06:00 PM` | `scripts/etf_weekly_digest.py`| 5-day net price delta ($, %), weekly trading range & 1-yr returns → `@achiETFBot` | [`systemd/achios-etf-weekly-digest.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-etf-weekly-digest.timer), [`scripts/etf_weekly_digest.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/etf_weekly_digest.py) |
| **`achios-email-digest`**| `08:30 AM` & `05:30 PM` | `scripts/email_digest.py` | VIP email triage across DLSU and Work inboxes (filters out Manila/Laguna noise) → `@achiSchooNounceBot` | [`systemd/achios-email-digest.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-email-digest.timer), [`scripts/email_digest.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/email_digest.py) |
| **`achios-evening-debrief`**| `12:00 MN` Daily | `scripts/evening_debrief.py`| Retrospective of completed tasks, commits, plus harvested rules card → `@achiOSBot` | [`systemd/achios-evening-debrief.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-evening-debrief.timer), [`scripts/evening_debrief.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/evening_debrief.py) |
| **`achios-vault-sync`**  | `*:00/15` (Every 15m) | `scripts/vault_inbox_sync.py` | Autonomous mobile capture sweep from `schoolMem/inbox/` and `achiMem/inbox/` to GitHub `origin/main` | [`systemd/achios-vault-sync.timer`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-vault-sync.timer), [`scripts/vault_inbox_sync.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/vault_inbox_sync.py) |
| **`achios-failure-alert@`**| On Failure (`%n`) | `scripts/service_failure_alert.py`| Captures journalctl crash logs, redacts bot tokens/keys, and delivers emergency alert | [`systemd/achios-failure-alert@.service`](file:///home/achibukz/Code/GitHub/AIS-OS/systemd/achios-failure-alert@.service), [`scripts/service_failure_alert.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/service_failure_alert.py) |

---

## 2. Universal TGDB (Telegram Database Archiver)

* **Design Contract:** Operating state lives in `AIS-OS`, but all conversation knowledge, decisions, and turn logs are permanently archived in Obsidian `achiMem/tgdb/YYYY-MM/`.
* **Multi-Engine Support:**
  * **Claude Code Sessions:** Tagged with `@achiOSClaudeBot` / `Claude 3.5 Sonnet` via `scripts/export_claude_transcripts.py`.
  * **Antigravity CLI Sessions:** Tagged with `@achiAgyOSBot` / `Gemini 3.7 Flash` via `src/bot.py` and `scripts/export_transcripts.py`.
  * **Hermes Sessions:** Hooked to gateway exports.
* **Sanitization:** Strips API tokens, bot secrets, and private paths prior to writing markdown frontmatter notes.
* **Key Files:**
  * [`AIS-OS/scripts/tgdb_logger.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/tgdb_logger.py)
  * [`AIS-OS/scripts/export_transcripts.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/export_transcripts.py)
  * [`AIS-OS/scripts/export_claude_transcripts.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/export_claude_transcripts.py)
  * [`achiMem/tgdb/2026-08/`](file:///home/achibukz/Documents/Obsidian/achiMem/tgdb/2026-08/)

---

## 3. Autonomous Correction Harvester & Self-Learning System

* **Concept:** Converts conversational friction, user corrections, and negative feedback into durable machine rules without requiring manual prompt engineering.
* **Pipeline:**
  1. `scripts/extract_corrections.py` runs on a scheduled cadence / evening debrief.
  2. Parses today's `tgdb/` transcripts looking for correction triggers (`"never do that again"`, `"stop doing X"`, `"why did you..."`, `"don't..."`).
  3. Uses model evaluation to extract root causes and formulate actionable, non-hallucinatory rules.
  4. Automatically appends validated rules to `AIS-OS/.agentrules` and logs rationale into `AIS-OS/decisions/log.md`.
  5. Delivers a secondary `🧠 Self-Learning & Harvested Rules` card during the midnight `evening_debrief`.
* **Key Files:**
  * [`AIS-OS/scripts/extract_corrections.py`](file:///home/achibukz/Code/GitHub/AIS-OS/scripts/extract_corrections.py)
  * [`AIS-OS/.agentrules`](file:///home/achibukz/Code/GitHub/AIS-OS/.agentrules)
  * [`AIS-OS/decisions/log.md`](file:///home/achibukz/Code/GitHub/AIS-OS/decisions/log.md)

---

## 4. `achiAgy` — Dedicated Google Antigravity CLI Telegram Daemon

Built from scratch in Python to bridge the interactive Google Antigravity (`agy`) CLI with Telegram.

* **Architecture:**
  * **Terminal UI Console (`src/tui.py`):** Runs inside tmux (`pts/11`) rendering live thought reasoning, tool call diffs, timing metrics, and step checkpoints.
  * **Session Manager (`src/session_manager.py`):** Maintains project-scoped conversations (`/project AIS-OS`, `/project achiAgy`, `/cd <path>`).
  * **Dot-Slash Command Interceptor:** Supports fast terminal shortcuts (`./new`, `./context`, `./usage`, `./projects`, `./status`, `./bypass`, `./cancel`).
  * **Process Supervisor (`scripts/run-bot.sh`):** Handles clean shutdown (`stop_running()`), graceful exit code `42`, and automatic reload loop to prevent HTTP 409 Conflict polling locks.
  * **Single-Message Delivery Protocol:** Confines interim tool spam to the tmux TUI; sends only the final complete answer to Telegram with standard push alerts.
* **Key Files:**
  * [`achiAgy/src/bot.py`](file:///home/achibukz/Code/GitHub/achiAgy/src/bot.py)
  * [`achiAgy/src/agy_client.py`](file:///home/achibukz/Code/GitHub/achiAgy/src/agy_client.py)
  * [`achiAgy/src/session_manager.py`](file:///home/achibukz/Code/GitHub/achiAgy/src/session_manager.py)
  * [`achiAgy/src/formatters.py`](file:///home/achibukz/Code/GitHub/achiAgy/src/formatters.py)
  * [`achiAgy/src/tui.py`](file:///home/achibukz/Code/GitHub/achiAgy/src/tui.py)
  * [`achiAgy/scripts/run-bot.sh`](file:///home/achibukz/Code/GitHub/achiAgy/scripts/run-bot.sh)

---

## 5. Notification Architecture & Operational Quirks (The "Ping" Audit)

### Channel & Bot Routing
1. **`@achiOSBot` (`8725294836`)**: System-level notifications, cron digests, and crash alerts configured via `~/.config/achios/telegram.env`.
2. **`@achiAgyOSBot` (`8832060896`)**: Interactive Antigravity AI pair programmer daemon.
3. **`@achiETFBot` / `@achiSchooNounceBot`**: Dedicated topic/feed channels for financial data and DLSU academic announcements.
4. **`@schoMemBot`**: School vault interactive bot running under `schoolmem_wiki_guard.py` (read-only enforcement for `wiki/`).

### Notification Quirks to Audit & Address
* **Multi-Bot Destination Confusion:** Scheduled alerts land in `@achiOSBot`, while chat turns occur in `@achiAgyOSBot`. If the user is active in one chat, Telegram suppresses sound/popups for the other.
* **Telegram Desktop Active Focus Suppression:** If Telegram Desktop or Web is open on a computer, Telegram marks messages as "read/viewed" and suppresses mobile push notifications.
* **Reply Threading vs Direct Messages:** In `achiAgy` commit `b8406c8`, `reply_to_message_id` was swapped for direct `bot.send_message()` to ensure mobile push notifications are not swallowed by Telegram client reply-threading settings.
* **In-Process Task/Timer Persistence on Restart:** `agy` CLI in-process background tasks are terminated during server restarts. Backlog task logged to integrate scheduling into OS-level systemd/cron or persistent SQLite queue.

---

## 6. Infrastructure, Server Hardening & Integrations

* **Hardware & OS:** HP 14-ac137TX (`achibuntu`), Intel Core i5-6200U, 8 GB RAM, 240 GB SSD running Ubuntu 24.04 LTS headless.
* **Remote Access:** Tailscale mesh network + Termius SSH access on iPhone/Mac; hardened SSH (key-only authentication, root login disabled).
* **Vault Multi-Writer Sync:** `achimem_capture.py` handles two-machine git sync (Mac ↔ Linux server) with autostash rebase and conflict-abort protection (51 test cases).
* **Google Workspace Multi-Account OAuth:** OAuth2 helper (`auth_google_account.py`) supporting headless pasteable redirect URLs for Personal (`akibukuhan10`), DLSU (`@dlsu.edu.ph`), and Work Google accounts.
* **CasaOS Dashboard:** Deployed with Filebrowser, Code-Server, and container monitoring.

---

## 7. Personal Projects & Operations Logged in Vault

* **ING Hubs Philippines Internship:** Accepted offer (Intern 1, Retail Tech, Oct 2026 – Mar 2027, ₱15,000/mo). Requirements tracking, BPI SaveUp routing, and faculty character reference outreach (`output/2026-08-18-*.md`, `output/2026-08-19-*.md`).
* **DLSU Academics:** Term 1 AY2627 schedule planning (CCINOV8, STDISCM, THS-ST2, STELEC4, GE) and enrollment task on Aug 25 (ID 123 2nd DL).
* **Health & Nutrition Domain:** Established `wiki/personal/health/` tracking workout split, progressive overload, macro targets, and high-protein recipes (`recipes.md`).

---

## 8. Suggested Questions & Directives for Claude Opus Review

1. **Architecture Cohesion:** Are there any redundant scripts or potential race conditions between `vault_inbox_sync.py`, `achimem_capture.py`, and the systemd timers?
2. **Notification Reliability:** Is there a cleaner architectural pattern to unify `@achiOSBot` and `@achiAgyOSBot` notification feeds or ensure mobile alerts are never suppressed?
3. **Error Resilience:** Are all systemd unit `Restart=` and `OnFailure=` policies airtight against network drops or Telegram API rate limits?
4. **Self-Learning Optimization:** Can the `extract_corrections.py` parsing logic be enhanced to prevent over-fitting or conflicting rules in `.agentrules`?
5. **Memory & Scaling:** How should session history and context windows be pruned over long multi-month operations?
