# Connections

Registry of every system achiOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | Tarsi (iOS money manager) + allowance | `export` — manual CSV backup dropped into `~/Downloads`, read on request. No API exists. | — | 2026-08-10 |
| 2 | Email | Gmail ×4 — main `aki.bukz12@gmail.com`, sub-main `akibukuhan10@gmail.com`, work `akibukzwork@gmail.com`, school `abram_bukuhan@dlsu.edu.ph` | connected — `gws gmail`, one config dir per account (see `references/gws-api.md`) | OAuth ×4, `~/.config/gws-{main,personal,work,dlsu}` | 2026-08-10 |
| 3 | Calendar | Google Calendar — 15 distinct calendars. Default to `gws-personal` (school, thesis, Personal, Bdayy, Canvas feed); `gws-dlsu` for DLSU event detail; `gws-work` to write to Job. | connected — `gws calendar`, full id table in `references/gws-api.md` | same four OAuth dirs | 2026-08-10 |
| 4 | Communication | Discord (thesis) + Messenger (school/personal groups) | not yet connected — DLSU mail moved to row 2 | — | — |
| 5 | Project / task tracking | Canvas LMS (school tasks) + achiMem (general — proposed) + achiOS (this repo, project specs) | partial — Canvas reachable via `/canvas-tracker` (Chrome session, see `~/.claude/CLAUDE.md` memory) | session cookie via Claude in Chrome | 2026-06-13 |
| 6 | Meeting intelligence | Thesis F2F notes → schoolMem/raw → schoolMem/wiki; class material likewise | partial — manual ingestion today; `ingest-batch` skill exists | — | — |
| 7 | Knowledge / files | achiMem (`~/Documents/Obsidian/achiMem`) — the single entry point. It hubs out to schoolMem, career-ops, and thesis; go through achiMem, not around it. | connected — local files + git; auto-capture via `scripts/achimem_capture.py`, recall via `scripts/achimem_recall.py` | — | 2026-08-10 |

| 8 | Notifications | Telegram — achiOS bot (its own bot, not Hermes') | `script` — `scripts/telegram_notify.py` is the shared sender; systemd user timers on achibuntu (`OnCalendar=… Asia/Manila`, `Persistent=true`). Not cron — it ignores `CRON_TZ`. Wire new jobs with the `cron-telegram` skill. **Also two-way**: the `telegram` plugin's channel runs Claude Code itself in this Telegram DM — Aki messages the bot from his phone, the session sees it as a `<channel source="plugin:telegram:telegram">` block and replies inline (`mcp__plugin_telegram_telegram__reply`), so achiOS is reachable from mobile without a terminal. Access gated by `/telegram:access` (allowlist/pairing in `~/.claude/channels/telegram/access.json`). **Two bots, one box** — `TELEGRAM_STATE_DIR` gives each its own token and allowlist: achiOS on the default dir, schoolMem (`@schoMemBot`) on `~/.claude/channels/telegram-schoolmem`, launched from the vault so its `CLAUDE.md` loads. Paired and working 2026-08-17. | bot token + chat id in `~/.config/achios/telegram.env`, mode 600; schoolMem token in its own state dir `.env`, mode 600 | 2026-08-17 |

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
