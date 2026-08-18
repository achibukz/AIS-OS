# Connections

Registry of every system achiOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | Tarsi (iOS money manager) + allowance | `export` — manual CSV backup dropped into `~/Downloads`, read on request. No API exists. | — | 2026-08-10 |
| 2 | Email | Gmail ×4 — main `aki.bukz12@gmail.com`, sub-main `akibukuhan10@gmail.com`, work `akibukzwork@gmail.com`, school `abram_bukuhan@dlsu.edu.ph` | connected — `scripts/email_digest.py` (DLSU, Work, Personal live on achibuntu via `~/.config/achios/google_token_{dlsu,work,}.json`) | OAuth ×3 on achibuntu (`~/.config/achios/`), OAuth ×4 on Mac (`~/.config/gws-*`) | 2026-08-18 |
| 3 | Calendar | Google Calendar — 15 distinct calendars. Default to `gws-personal` (school, thesis, Personal, Bdayy, Canvas feed); `gws-dlsu` for DLSU event detail; `gws-work` to write to Job. | connected — `scripts/daily_brief.py` & `scripts/evening_debrief.py` reading DLSU, Personal, Work tokens | OAuth ×3 on achibuntu (`~/.config/achios/`) | 2026-08-18 |
| 4 | Communication | Discord (thesis) + Messenger (school/personal groups) | not yet connected — DLSU mail moved to row 2 | — | — |
| 5 | Project / task tracking | Canvas LMS (school tasks) + achiMem (general — proposed) + achiOS (this repo, project specs) | partial — Canvas reachable via `/canvas-tracker` (Chrome session, see `~/.claude/CLAUDE.md` memory) | session cookie via Claude in Chrome | 2026-06-13 |
| 6 | Meeting intelligence | Thesis F2F notes → schoolMem/raw → schoolMem/wiki; class material likewise | partial — manual ingestion today; `ingest-batch` skill exists | — | — |
| 7 | Knowledge / files | achiMem (`~/Documents/Obsidian/achiMem`) — the single entry point. It hubs out to schoolMem, career-ops, and thesis; go through achiMem, not around it. | connected — local files + git; auto-capture via `scripts/achimem_capture.py`, recall via `scripts/achimem_recall.py` | — | 2026-08-10 |

| 8 | Notifications | Telegram — six bots, see **naming registry** below | `script` — `scripts/telegram_notify.py` is the shared sender for cron/one-way notifications; systemd user timers on achibuntu (`OnCalendar=… Asia/Manila`, `Persistent=true`). Not cron — it ignores `CRON_TZ`. Wire new jobs with the `cron-telegram` skill. **Also two-way**: the `telegram` plugin's channel runs Claude Code itself in a Telegram DM — Aki messages a bot from his phone, the session sees it as a `<channel source="plugin:telegram:telegram">` block and replies inline (`mcp__plugin_telegram_telegram__reply`). Access gated by `/telegram:access` (allowlist/pairing per bot's own `access.json`). **Named state dirs, one per bot** — `TELEGRAM_STATE_DIR` gives each its own token and allowlist: `~/.claude/channels/telegram-achios` and `telegram-schoolmem`. No token may live in the plugin's default `~/.claude/channels/telegram/` — see **Telegram bots** in `CLAUDE.md` for why. The two Claude Code bots run unattended as systemd user units inside their own tmux servers — `achios-bot` (`tmux -L achios`, reads and writes) and `achios-schoolmem-bot` (`tmux -L schoolmem`, write-blocked out of `wiki/`) — restarting daily at 04:10 and 04:00 Manila. Live 2026-08-17. Pairing is one-time; ids persist in each bot's `access.json`. | bot token + chat id in `~/.config/achios/telegram.env` (achinouncements), mode 600; each other bot's token in its own state dir `.env`, mode 600 | 2026-08-17 |

## Telegram bots — naming registry

Six identities Aki uses to talk about these bots. Verified against each `getMe` on 2026-08-17
— the Telegram `@username` is the source of truth if this table and a bot ever disagree.

| Aki's name | Telegram | Tool | Scope | Purpose | Status |
|---|---|---|---|---|---|
| achiOS | `@achiOSClaudeBot` | Claude Code | AIS-OS repo | Two-way chat, read + write, no guard | live |
| schoolMem | `@schoMemBot` | Claude Code | schoolMem vault | Two-way chat, write-blocked out of `wiki/` | live |
| achiOS AGY | `@achiAgyOSBot` | agy (Google Antigravity) | AIS-OS repo | Two-way chat via `achiAgy` | live, built 2026-08-17 |
| schoolMem AGY | `@schoMemAGYBot` | agy (Google Antigravity) | schoolMem vault | Two-way chat via `achiAgy` | live, built 2026-08-17 |
| achinouncements | `@achiOSBot` | Claude Code (cron only) | AIS-OS `scripts/telegram_notify.py` | One-way: daily brief + scheduled/cron jobs | live |
| achiFinance | Dedicated bot | Python (`voo_digest.py`) | AIS-OS | One-way: ETF market digests (VOO, VXUS, QQQM) via `telegram_finance.env` | live |
| achiSchoNounce | `@achiSchoNounceBot` | Python (`email_digest.py`) | schoolMem / DLSU | One-way: DLSU academic emails & school announcements via `telegram_school.env` | live |
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
