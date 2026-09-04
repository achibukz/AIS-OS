# Connections

Registry of every system achiOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | Tarsi (iOS money manager) + allowance | `export` — manual CSV backup dropped into `~/Downloads`, read on request. No API exists. | — | 2026-08-10 |
| 2 | Email | Gmail ×4 — main `aki.bukz12@gmail.com`, sub-main `akibukuhan10@gmail.com`, work `akibukzwork@gmail.com`, school `abram_bukuhan@dlsu.edu.ph` | connected — `scripts/email_digest.py` via `gws` CLI | OAuth ×4 in Production mode on achibuntu (`~/.config/gws-*`) | 2026-09-05 |
| 3 | Calendar | Google Calendar — 15 distinct calendars. Default to `gws-personal` (school, thesis, Personal, Bdayy, Canvas feed); `gws-dlsu` for DLSU event detail; `gws-work` to write to Job. | connected — `scripts/daily_brief.py` & `scripts/evening_debrief.py` via `gws` CLI | OAuth ×4 in Production mode on achibuntu (`~/.config/gws-*`) | 2026-09-05 |
| 4 | Cloud Storage | Google Drive ×4 — main, personal, work, dlsu | connected — `gws drive` CLI across all four profiles (file listing, download, upload) | OAuth ×4 in Production mode on achibuntu (`~/.config/gws-*`) | 2026-09-05 |
| 5 | Communication | Discord (thesis) + Messenger (school/personal groups) | not yet connected — DLSU mail moved to row 2 | — | — |
| 6 | Project / task tracking | Canvas LMS (school tasks) + achiMem (general — proposed) + achiOS (this repo, project specs) | partial — Canvas reachable via `/canvas-tracker` (Chrome session, see `~/.claude/CLAUDE.md` memory) | session cookie via Claude in Chrome | 2026-06-13 |
| 7 | Meeting intelligence | Thesis F2F notes → schoolMem/raw → schoolMem/wiki; class material likewise | partial — manual ingestion today; `ingest-batch` skill exists | — | — |
| 8 | Knowledge / files | achiMem (`~/Documents/Obsidian/achiMem`) & schoolMem (`~/Documents/Obsidian/schoolMem`) — the single entry point. Hubs out to schoolMem, career-ops, and thesis. | connected — Syncthing (P2P real-time sync between Achibuntu & AchiBook Air over LAN/Tailscale) + Samba share (`smb://100.106.210.38` / Finder) + local git; auto-capture via `scripts/achimem_capture.py`, recall via `scripts/achimem_recall.py` | — | 2026-08-26 |
| 9 | Notifications | Telegram — six bots, see **naming registry** below | `script` — `scripts/telegram_notify.py` is the shared sender for cron/one-way notifications; systemd user timers on achibuntu (`OnCalendar=… Asia/Manila`, `Persistent=true`). Not cron — it ignores `CRON_TZ`. Wire new jobs with the `cron-telegram` skill. **Also two-way**: the `telegram` plugin's channel runs Claude Code itself in a Telegram DM — Aki messages a bot from his phone, the session sees it as a `<channel source="plugin:telegram:telegram">` block and replies inline (`mcp__plugin_telegram_telegram__reply`). Access gated by `/telegram:access` (allowlist/pairing per bot's own `access.json`). **Named state dirs, one per bot** — `TELEGRAM_STATE_DIR` gives each its own token and allowlist: `~/.claude/channels/telegram-achios` and `telegram-schoolmem`. No token may live in the plugin's default `~/.claude/channels/telegram/` — see **Telegram bots** in `CLAUDE.md` for why. The two Claude Code bots run unattended as systemd user units inside their own tmux servers — `achios-bot` (`tmux -L achios`, reads and writes) and `achios-schoolmem-bot` (`tmux -L schoolmem`, write-blocked out of `wiki/`) — restarting daily at 04:10 and 04:00 Manila. Live 2026-08-17. Pairing is one-time; ids persist in each bot's `access.json`. | bot token + chat id in `~/.config/achios/telegram.env` (achinouncements), mode 600; each other bot's token in its own state dir `.env`, mode 600 | 2026-08-17 |

## Telegram bots — naming registry

Six identities Aki uses to talk about these bots. Verified against each `getMe` on 2026-08-17
— the Telegram `@username` is the source of truth if this table and a bot ever disagree.

| Aki's name | Telegram | Tool | Scope | Purpose | Status |
|---|---|---|---|---|---|
| achiOS | `@achiOSClaudeBot` | Claude Code | AIS-OS repo | Two-way chat, read + write, no guard | live |
| schoolMem | `@schoMemBot` | Claude Code | schoolMem vault | Two-way chat, write-blocked out of `wiki/` | live |
| achiOS AGY | `@achiAgyOSBot` | agy (Google Antigravity) | `~/Code/GitHub` | Two-way chat via `achiAgy` across GitHub repos | live, repointed to `~/Code/GitHub` 2026-08-27 |
| schoolMem AGY | `@schoMemAGYBot` | agy (Google Antigravity) | schoolMem vault | Two-way chat via `achiAgy` | live, built 2026-08-17 |
| achinouncements | `@achiOSBot` | Claude Code (cron only) | AIS-OS `scripts/telegram_notify.py` | One-way: daily brief + scheduled/cron jobs | live |
| achiFinance | `@achiETFBot` | Python (`voo_digest.py`, `etf_weekly_digest.py`) | AIS-OS | One-way: Daily ETF market digests (08:00 & 22:00) + Sunday weekly recap (18:00) via `telegram_finance.env` | live |
| achiSchoNounce | `@achiSchooNounceBot` | Python (`email_digest.py`) | schoolMem / DLSU | One-way: DLSU academic emails & school announcements via `telegram_school.env` | live |
| achiHermes | not yet created | Codex (planned) | Hermes agent | Hermes bot, to be powered by Codex once he has a subscription | planned |

`achiAgy` (`~/Code/GitHub/achiAgy`) is a separate repo from AIS-OS that wraps `agy` for
Telegram, mirroring the achiOS bot pattern one-for-one — tmux commands for all four live
bots are in achiMem's [[achi-os]] page, not duplicated here.

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `not yet connected`.

When you wire a new tool, also save `references/{tool}-api.md` capturing endpoints, auth flow, and common queries — researched-once-saved-forever.

## Financials — how Aki organizes money

Tarsi, iOS, PHP, single-user. Backup export is one flat CSV where every row carries a
`recordType` (`account`, `customCategory`, `customSubcategory`, `expense`, `income`,
`transfer`, `recurringExpense`, `recurringIncome`, `metadata`) and only the columns for
that type are filled. Category names live in `label`, not `name`. Transactions reference
categories by id, so resolve `id → label` before reporting anything.

- **Accounts (19).** Spending: Cash, GCash. Digital banks: Tonik, Tonik Emergency Stash,
  GoTyme, GoTyme GoSave, CIMB. Prepaid/stored-value treated as accounts: Starbucks, Zus,
  Beep, TZ, QPS. Sinking fund: "Pls Save Aki". Investments held as accounts with
  `type` `stocks`/`crypto`: VOO, QQQ, VXUS, BTC, ETH, SOL — all at 0 today.
- **Expense categories.** Drinks, 🍜 Food (subs: Dinner, Eating out, Lunch, Beverages),
  Transportation (Subway, Taxi, Bus, Car), Social Life (Friend, Dues, Fellowship, Alumni),
  Sweet Treat, Climbing, Gym, Tech, Gambling, Games, Parking, Flowers, other, fees.
- **Income** is uncategorized — allowance and transfers in, tagged only by account.
- History runs 2024-09-24 → present, ~1,500 transactions.

Not connected and not connectable — Tarsi has no API. When Aki wants analysis he drops a
fresh `tarsi-backup-*.csv` and says so. Don't assume a stale export is current.

## Related repos (reachable through achiMem)

achiMem is the hub. Its `wiki/personal/` pages already bridge to each of these, so start
there rather than opening repos blind.

- `~/Documents/Obsidian/achiMem` — general vault, **the entry point**. `index.md` lists hub pages.
- `~/Documents/Obsidian/schoolMem` — school notes + thesis meeting minutes. Bridged by `wiki/personal/school-context.md`.
- `~/Code/GitHub/career-ops` — application pipeline, CV/cover letter generation, follow-up cadence. Bridged by `wiki/personal/career-ops-hub.md`. `data/applications.md` is the source of truth for active applications.
- `~/Code/GitHub/sfv-thesis` — thesis source, chapters, dataset pipeline.

### achi-files — centralized documents and media store (added 2026-08-28)

- Path: `~/Documents/Files/` on achibuntu and AchiBook Air. No Git repo; Syncthing is the only sync.
- Syncthing folder id `achi-files`, label `Documents Files`, `sendreceive`, fsWatcher on with a 10s
  delay, 3600s rescan, simple versioning cleaned after 30 days. Shared achibuntu ↔ AchiBook Air.
- Managed through the Syncthing REST API at `127.0.0.1:8384`, never by editing `config.xml` by hand.
- Reachable over Tailscale at `http://100.106.210.38:8999/Documents/Files/...`, verified 200 for both
  an image and a PDF.
- achiAgy's `MediaDispatcher` sends anything under here to Telegram already, no change needed.
- `personal/legal/` and `personal/finance/` are in the viewer's `BLOCKED_PATTERNS` and return 403.
  Telegram still delivers them; only the link is withheld. Keep `VIEWER_BLOCKED_SUBPATHS` in
  `achiAgy/src/media_dispatcher.py` in step with the viewer's list.
- The vault folder `varww-m4imt` now ignores `.git` and `*.sync-conflict-*`. Set it on any new device
  before first sync, or that device will start replicating git metadata again.

### Immich photo management & folder album sync (added 2026-09-02)

- Self-hosted Immich server reachable at `http://100.106.210.38:2283` (Docker container `immich-server`).
- External Library: `/home/achibukz/Documents/Files/personal/memories` mounted to `/mnt/media/memories`.
- Folder-to-Album Sync: `salvoxia/immich-folder-album-creator:latest` via `scripts/immich_folder_sync.sh` (`--dry-run` supported).
- Schedule: `systemd/achios-immich-sync.timer` (runs daily at `00:30 Asia/Manila` with `Persistent=true`).
- Log: `~/.local/state/achios/immich_sync.log`.
- Config: `ALBUM_LEVELS=1`, maps all 114 `YY.MM.DD- EventName` folders to chronological Immich albums (7,018+ assets). Automatically triggers external library scan before syncing albums.

### Google Workspace & Google Drive (production mode, verified 2026-09-05)

- GCP project `achiclaude` OAuth consent screen promoted to **In Production** status.
- Refresh tokens are permanent; the 7-day expiration policy for testing-mode apps is eliminated.
- Mechanism: `gws` CLI (`~/.npm-global/bin/gws`) with `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-<profile>` and `KEYRING_BACKEND=file`.
- Four authenticated profiles on Achibuntu:
  - `gws-main`: `aki.bukz12@gmail.com` (Gmail, Drive)
  - `gws-personal`: `akibukuhan10@gmail.com` (Gmail, Calendar, Drive)
  - `gws-work`: `akibukzwork@gmail.com` (Gmail, Calendar, Drive)
  - `gws-dlsu`: `abram_bukuhan@dlsu.edu.ph` (Gmail, Calendar, Drive)
- Verified active scopes: Gmail (`https://www.googleapis.com/auth/gmail.*`), Google Calendar (`https://www.googleapis.com/auth/calendar`), and Google Drive (`https://www.googleapis.com/auth/drive`).

## Codex global writing hook

Added 2026-08-29 at `/home/achibukz/.codex/hooks.json`. A SessionStart command prints Aki's unslop instruction as JSON additional context. The command output is verified; activation awaits Aki's trust approval through `/hooks`. No network endpoint or credentials. Claude Code settings are unchanged.
