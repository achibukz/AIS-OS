# Tauri Desktop GUI for achiOS, achiCore, and achiMem Architecture & Blueprint

**Date:** 2026-08-30  
**Status:** Scoped / Draft  
**Target Platform:** macOS (AchiBook Air) connecting to Linux server (Achibuntu) via SSH / Tailscale  
**Tech Stack:** Tauri v2, Rust (`russh` / `ssh2`), React / Vite / Tailwind CSS

---

## 1. System Overview

The desktop control center provides a native macOS GUI to monitor, orchestrate, and manage all components across the personal AI operating system:
1. **achiOS (AIS-OS):** Task tracking register ([tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md)), daily brief schedules, cron jobs, and Google Calendar sync.
2. **achiCore / achiAgy:** Multi-agent Telegram hub, active topic settings, model switching, reason efforts, sandbox modes (`accept-edits` vs `plan`), and active turn streaming.
3. **achiMem / schoolMem:** Declarative memory inspection (`USER.md`, `MEMORY.md`), learning ledger stream, and deep links into the Tailscale Markdown viewer.

---

## 2. Core GUI Views & Capabilities

### View A: Live Agent Kanban & Activity Monitor
- **Real-time Agent States:** Reads active session locks and files from `~/.local/state/achicore/`.
- **Kanban Columns:**
  - `Idle`: Standby topics awaiting prompts.
  - `Running (Mid-Turn)`: Actively executing tool calls or reasoning.
  - `Blocked / Waiting`: Stuck on permissions, quota cooling, or failed dependencies.
  - `Completed`: Last finished turns with token usage and duration stats.
- **Agent Cards:** Details topic identity (`#Aea`, `#Luna`, `#Atlas`, `#Ari`, `#Ara`, `#Aurora`), active workspace directory, current branch/ticket, and streaming tool logs.
- **Turn Controls:** Abort/cancel stuck turns, clear context with `/new`, or dispatch delegations directly from desktop.

### View B: Topic & Model Orchestration Matrix
- **Matrix View:** Lists all topics defined in `achiCore/src/topic_router.py` and persistent state.
- **Dynamic Topic Controls:**
  - **Model:** Switch between `gemini-3.7-flash-high`, `claude-sonnet-4-6`, `gemini-3.1-pro-high`, `gpt-5.6-luna`, etc.
  - **Reasoning Effort:** Toggle between `high`, `medium`, `low`.
  - **Execution Mode:** Toggle between `accept-edits` (full tool access) and `plan` (read-only sandbox).
  - **Workspace:** Switch active repository directory.
  - **Persona / System Prompt:** View and edit system markdown prompts.

### View C: Visual Task Register (Two-Way [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) Sync)
- **Bidirectional Parser:** Reads and writes [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) maintaining strict formatting `- [ ] What to do #area !priority @YYYY-MM-DD`.
- **Interactive Views:**
  - Semantic category groupings (`#achicore`, `#career`, `#school`, `#infra`, `#asa`, `#finances`).
  - Kanban board by status: Active (`- [ ]`), Blocked (`- [~]`), Done (`- [x]`).
  - Priority and calendar date filters.
- **Google Calendar Trigger:** One-click insertion for dated tasks into designated calendars via `scripts/gcal_add.py`.

### View D: Memory & Knowledge Hub
- **Declarative Memory Budget:** Visual progress meter tracking 2,500-character limits for `~/.config/achios/USER.md` and `~/.config/achios/MEMORY.md`.
- **Learning Ledger Feed:** Real-time stream of candidate rules from `~/.local/state/achios/learning_ledger.jsonl`.
- **Viewer Deep Links:** Clickable document links opening notes in the Tailscale Markdown viewer (`http://100.106.210.38:8999/`).

### View E: Quotas & Systemd Service Health
- **Engine Quotas:** Live gauge of Gemini, Codex, and Claude rate limits, cooling timers, and active fallback chains.
- **Systemd Daemons:** Monitor and restart `achicore.service`, `achios-daily-brief.timer`, `achios-vault-sync.timer`, `syncthing`, and `tailscaled`.

---

## 3. Network & Connection Architecture

```
┌────────────────────────────────────────────────────────┐
│                   AchiBook Air (Mac)                   │
│                                                        │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │   Frontend UI        │    │    Tauri Backend     │  │
│  │ (React / Svelte UI)  │◄──►│    (Rust Engine)     │  │
│  └──────────────────────┘    └──────────┬───────────┘  │
└─────────────────────────────────────────┼──────────────┘
                                          │ SSH / Tailscale
                                          ▼
┌────────────────────────────────────────────────────────┐
│                   Achibuntu (Linux)                    │
│                                                        │
│  • ~/Code/GitHub/AIS-OS/tasks.md (Tasks Register)       │
│  • ~/.local/state/achicore/ (Active Session & Locks)   │
│  • ~/.config/systemd/user/ (Systemd Daemons)           │
│  • achiMem & schoolMem Vaults                          │
└────────────────────────────────────────────────────────┘
```

1. **Rust SSH/SFTP Client:**
   - Uses `russh` or `ssh2` in the Tauri Rust core.
   - Authenticates using the local macOS private key (`~/.ssh/id_ed25519`).
   - Handles remote file reads/writes (SFTP), command execution, and remote log tailing over persistent SSH channels.
2. **Tailscale API Integration (Optional / Hybrid):**
   - Direct HTTP/WebSocket connection to `100.106.210.38:<port>` when on Tailscale for low-latency state pushes and `inotify` file watching.
   - Falls back to pure SSH when the server-side web daemon is stopped.

---

## 4. Implementation Plan & Milestones

1. **Phase 1: Tauri v2 Scaffold & SSH Engine**
   - Initialize Tauri v2 project with React/Vite/Tailwind.
   - Implement Rust SSH/SFTP connector with key-based authentication to Achibuntu.
2. **Phase 2: Task Register & Topic Settings Panel**
   - Build two-way parser for [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md).
   - Build topic matrix view reading and mutating `~/.local/state/achicore/topics.json`.
3. **Phase 3: Live Agent Kanban & Log Streaming**
   - Implement remote file polling / log tailing for active agent sessions.
   - Render Kanban cards with live tool execution output.
4. **Phase 4: Memory Inspector & Systemd Controls**
   - Add budget meters for `USER.md` and `MEMORY.md`.
   - Add systemd user unit status checks and restart commands.
