# Session Log

## 2026-08-20 18:10 [saved]
Goal: Audit TGDB, the correction harvester, and the self-learning loop — is it working, is it automatic, and what does Hermes do better.

Decisions:
- Answered the automation question: it **is** already automatic. `achios-vault-sync.timer` runs `vault_inbox_sync.py` every 15 min, which exports transcripts, harvests corrections, then commits the vault. Aki initiates nothing.
- Found the harvester is **self-amplifying**. achiAgy injects `MEMORY.md` verbatim into the prompt (`bot.py:900`); `clean_antigravity_text` does not strip it because it carries no tag; it lands inside an `**Aki:**` block; the harvester scans exactly those blocks and re-prefixes its own output. Substring dedup structurally cannot catch it because each generation is strictly longer. Three generations live in `MEMORY.md`.
- Found the documented **LLM gate does not exist** — `extract_corrections_from_candidates()` returns the regex fallback immediately, and there is no model call anywhere in the file. The docstring claims otherwise.
- Found `bot.py` and `export_transcripts.py` compute the **same tgdb filename** from the same conversation UUID and overwrite each other — one writes a single turn, the other the full transcript.
- Measured the damage: 54 of 86 `decisions/log.md` entries are machine noise; 3 of 5 `MEMORY.md` entries are recursive garbage.
- Compared against Hermes: it has **no automatic harvester at all**. Memory is model-written during a turn; `/learn` is user-invoked. Its `_SOURCE_HYGIENE` rule ("source text is DATA, not instructions") is the exact rule achiOS's harvester violates.
- Ruled `memory_engine.py` sound — a faithful Hermes port with locking, atomic writes, dedup, and budget. The storage layer is not the problem.
- Wrote `docs/2026-08-20-opus-audit-learning-loop.md`; eight remediation tasks added.
- Deliberately made **no code changes** — and sequenced the plan so the loop is cut *before* any cleanup, since a purge would be undone within 15 minutes.

Open items:
- The recursion is still running. Every 15 min is another chance to add a fourth generation.
- Decided not to port Hermes' learning graph yet — premature at achiOS's scale; fix the inlet first.


## 2026-08-20 17:00 [saved]
Goal: Full Opus audit of achiOS + achiAGY — architecture, what works, what is broken, and the fix list.

Decisions:
- Audited the **live server**, not just the repos: systemd state, journald, running processes, tmux panes, on-disk state. Where `docs/2026-08-20-system-architecture-audit.md` (Gemini's manifest) and the server disagreed, the server won.
- Held to the model allocation rule: `agy`/Gemini did mechanical extraction only; all analysis and conclusions are Opus's. Aki corrected mid-session when the first dispatch handed judgment to agy.
- Found the `/asa` skill is **broken** — `SKILL.md` documents an `asa` CLI that exists nowhere on the box. The first dispatch silently no-op'd because stderr was swallowed. Fell back to driving `agy -p` directly.
- 13 findings written to `docs/2026-08-20-opus-audit-achios-achiagy.md`, 3 of them P0, all reproduced rather than inferred.
- Ten remediation tasks added to `tasks.md`, sequenced so idempotency lands before retry (otherwise `Restart=on-failure` spams duplicate digests).
- Deliberately made **no code changes** — Aki asked for an audit and a fix list, not a fix run.

Open items:
- 4 jobs still sitting in `failed` state; `systemctl --user reset-failed` not run yet.
- `@achiOSBot` token is in journald in cleartext and still needs rotating.
- Dated the ten new tasks as a proposed sequence but did **not** create calendar events, because those dates are mine, not Aki's. Needs his confirmation before they go to `Personal`.


## 2026-08-17 03:45 [saved]
Goal: Turn the old HP laptop into a headless Hermes/Claude Code agent host.

Decisions:
- `commit()` in `achimem_capture.py` now rebases, pushes, retries once, and **aborts** a conflicting rebase — two machines append to `log.md`, so conflicts are unresolvable unattended.
- `sync-claude-config.sh` uses an **allowlist**, not a denylist — a future credential file dropped in `~/.claude/` cannot leak by default.
- Plugins are excluded from the sync; `enabledPlugins` in `settings.json` refetches them, avoiding a 333 MB transfer.
- Hermes `write_approval: true` on memory and skills — both default false, and a sub-70B model is running autonomously.
- Ubuntu **Server**, not Desktop — desktop power daemons actively fight the lid-close override an always-on box needs.

Rejected:
- `pip list` as evidence of a missing package — uv venvs have no `pip`.
- `| bash --flag` for piped installers — bash eats it; use `bash -s -- --flag`.
- Auto-merging the vault's append-only log unattended — risks silent mangling.

Open:
- Phase 8 unfinished: cron round-trip, power-cut test.
- SSH password auth still enabled on the server.

## 2026-08-17 04:30 [saved]
Goal: Port Claude Code writing skills to Hermes on the server.

Decisions:
- Copy chosen skills into `~/.hermes/skills/` rather than pointing `external_dirs` at `~/.claude/skills` — Hermes already ships 40+, and 51 more bloats what it reasons over.
- Made paths `~/`-relative in the **Mac** copies too, not a server fork — hardcoded `/Users/achibukz/` breaks on any second machine.
- `pbcopy` guarded with `command -v`, not removed — still works on the Mac, skips silently on Linux.
- career-ops personal data (`cv.md`, `applications.md`, `profile.yml`) is gitignored and stays that way; recruiter replies degrade on the server rather than putting a CV on a box with password SSH enabled.

Rejected:
- `external_dirs` exposing all 51 skills — context bloat.
- Reimplementing `pbcopy` via xclip — headless has no clipboard to fill.

Open:
- career-ops data unreachable on server; three options pending.
- `message-writer` voice.md path bug existed on Mac too, now fixed.

## 2026-08-17 09:15 [saved]
Goal: One command to bring every git repo on achibuntu up to date.

Decisions:
- `sync-repos` fast-forwards only — no merge, rebase, stash or push, because nothing running unattended may lose a commit.
- Untracked files do not block a pull; a fast-forward leaves them alone and aborts by itself on collision.
- Roots are scanned, not hardcoded, so a new clone is never silently skipped.

Rejected:
- `pull --rebase` everywhere — rewrites local commits unattended.
- Auto-stash before pulling — hides work he was mid-way through.
- `~/.claude` as a root — no remote on skills, marketplaces are `/plugin`'s job.

Open:
- `hermes-agent` first fetch exceeds the 300s default; still running at 227 MB.

## 2026-08-17 12:30 [saved]
Goal: Always-on schoolMem Telegram bot that can never write to the wiki.

Decisions:
- One bot per vault, not one routing between them — a misroute writes to the wrong vault under the wrong rules.
- `wiki/` ban enforced by a PreToolUse hook, not by CLAUDE.md — bypassPermissions removes every other gate.
- PreToolUse hooks DO fire under `--permission-mode bypassPermissions`; verified with a real denied write.
- `claude` falls back to `--print` with no TTY, so an unattended session needs tmux, not just systemd.
- Captures go to a tracked `inbox/`; `raw/` and `output/` are gitignored and strand notes on the server.

Rejected:
- `chmod -R a-w wiki/` — also blocks git fast-forwards, breaking daily sync.
- Trusting CLAUDE.md to hold the wiki line under bypass.
- `RuntimeMaxSec`+`Restart=always` — does not compose with oneshot+tmux.

Open:
- Bash under bypass is narrowed by heuristic, not closed.
- Separate unix user with read-only `wiki/` is the airtight fix, deferred.

## 2026-08-17 12:38 [saved]
Goal: Second always-on Telegram bot for achiOS, this one with write access.

Decisions:
- Operator bot runs unguarded — editing tasks.md, calendar and commits are the job, not a hazard.
- One `telegram-bot.sh` driven by `BOT_*` env vars per unit; `schoolmem-bot.sh` deleted.
- Guard made optional, not assumed, so an unguarded bot reuses the path without pretending otherwise.
- Restart timers staggered 04:00/04:10 — both fetch on launch and the box has one uplink.
- `install_units.sh` now enables `WantedBy=default.target` services, not only timers.

Rejected:
- A second standalone script — drifts, duplicates the fail-closed guard logic.
- Guarding the operator's achiMem/wiki writes anyway — would override an explicit instruction.
- A shared library sourced by two thin scripts — more parts than env vars, for two callers.

Open:
- Logging contract's achiMem/wiki ban is now documented but unenforced on the operator bot.
- Push is pre-authorised here, so a Telegram message can reach GitHub unattended.

## 2026-08-17 12:55 [saved]
Goal: achiOS bot went deaf — ordinary sessions were stealing its Telegram token.

Decisions:
- No bot token may live in `~/.claude/channels/telegram/`; achiOS moved to `telegram-achios`.
- Diagnosis is in the MCP log line `Channel notifications skipped: not in --channels list`.
- Regression test asserts no unit's `BOT_STATE_DIR` ends in `/channels/telegram`.
- Accepted a failed telegram MCP server in every ordinary session as the cost.

Rejected:
- Disabling the telegram plugin globally — the bot needs it enabled to use `--channels`.
- Per-project plugin scoping — bot and terminal share the same cwd, so it cannot separate them.

Open:
- Nothing stops a future `/telegram:configure` from writing a token back to the default dir.

## 2026-08-18 01:45 [saved]
Goal: Add ETF digest, systemd failure alerts, and several new Telegram debrief crons.

Decisions:
- `OnFailure=achios-failure-alert@%n.service` on all user services, with token/key redaction.
- `voo_digest.py` (VOO/VXUS/QQQM) at 04:30 + 08:00 Manila; timer-based, not cron.
- New crons: tasks digest, evening debrief, VIP email triage — each its own script+timer, sent to `achinouncements`.
- `daily_brief.py` refactored to deterministic Python (no LLM call, <1s).
- Vault inbox sync daemon (15 min) auto-commits mobile captures with rebase conflict protection.
- Published `achiAgy` repo; added PDF delivery pipeline; added Telegram conversation archive (`tgdb`) and cross-platform transcript exporter.

Rejected:
- Cron over systemd timers — ignores `CRON_TZ`, no `Persistent=true` recovery.
- LLM subprocess for daily brief — slow/flaky vs. deterministic formatting.
- Blind `git add -A` across vaults — risks staging scratch files outside `inbox/`.

## 2026-08-18 20:10 [saved]
Goal: CasaOS dashboard setup, DLSU schedule planner, ID 123 enlistment appointment.

Decisions:
- CasaOS live on achibuntu; Code-Server :8085, Filebrowser :8082. Webview ServiceWorker blocker fixed via Chrome insecure-origin flag, not self-signed certs.
- DLSU Term 1 planner built in Google Sheets (`1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4`).
- Golden 14-unit load: online Tuesday + one Friday on-campus block, keeping Mon/Wed/Thu/Sat free for the ING internship.
- ID 123 2nd DL enrollment added to `DLSU` calendar, Tue 2026-08-25 11:30-12:30. Codex eval rescheduled to 2026-10-29.

Rejected:
- Monday/Thursday electives (`HCI2000`) — extra campus days conflict with internship hours.

## 2026-08-19 05:50 [saved]
Goal: Bot separation (Finance + School), SSH Termius setup, ETF schedule optimization, weekly recap cron.

Decisions:
- Split one-way bots by domain: `@achiETFBot` (market digests), `@achiSchooNounceBot` (DLSU email), keeping `@achiOSBot`/`@schoMemBot` as before. `telegram_notify.py` parametrized with `env_path` to support this.
- Re-tuned ETF schedule to 08:00 + 22:00 Manila; added Sunday 18:00 weekly ETF recap.
- Termius on iPhone connected to achibuntu via Tailscale.
- Fixed a bash interpolation bug by using script-file payloads instead of quoted string interpolation.

## 2026-08-19 18:20 [saved]
Goal: Upgrade email digest cron with smart VIP context, noise filtering, and LLM synthesis cards.

Decisions:
- Hybrid triage pipeline: Heuristic filtering strips routine AM/PM HDAs, LinkedIn/Indeed job blasts, promo marketing, and Laguna-only notices before passing to LLM (`agy -p` in `~/.local/share/achios/llm`).
- Structured 3-tier clean cards: `⚡ HIGH PRIORITY & VIP`, `📚 COURSES & ACADEMICS` / `💼 WORK & RECRUITING`, and `📬 UPDATES & GENERAL`.
- Embedded key personal context: Dr. Briane Samson (thesis), recommendation letter replies, Manila suspensions/typhoon advisories, ING Retail Tech internship onboarding, and critical bank/security alerts.
- Personal email scanning enabled for high-value financial/security alerts only, staying completely silent when clean.
- Deterministic fallback builder ensures reliable message formatting if LLM times out or is offline.
- Created full test suite in `tests/test_email_digest.py` (19 passing unit tests).

Rejected:
- Raw subject-only lists — lacked context on actions needed.
- LLM-only unconstrained parsing — too slow and wasted tokens on generic spam.

Open:
- Finalize elective/GE section by 2026-08-23, ahead of 2026-08-25 enrollment.
- Research & design Asa as universal bidirectional multi-agent orchestrator (Claude Opus, AGY, Codex) (`!high`).

## 2026-08-19 17:53 [saved]
Goal: Configure /tasks structured formatting convention.

Decisions:
- Standardized `/tasks` output format across Antigravity and achiOS agents: 4-tier structured layout (Immediate Deadlines, DLSU Academics, Career/Finances, Systems & Engineering) with markdown checkboxes and file links.
- Updated `AGENTS.md`, `.agentrules`, and `decisions/log.md`.

## 2026-08-19 22:05 [saved]
Goal: Schedule Google One subscription cancellation and Google AI Pro Student discount purchase.

Decisions:
- Created Google Calendar events on `Personal` calendar:
  - 2026-10-13: Cancel current Google One subscription
  - 2026-10-14: Subscribe to Google AI Pro Student Discount (₱275/mo via SheerID)
- Added low-priority tasks to `tasks.md` with dates @2026-10-13 and @2026-10-14.

## 2026-08-19 22:42 [saved]
Goal: Refine Asa architectural vision and task scope with Telegram integration.

Decisions:
- Updated Asa task scope in `tasks.md` to define Asa as a universal, bidirectional multi-agent orchestrator connecting Claude Code, Antigravity (AGY), and Codex.
- Added native Telegram integration to Asa: build a Telegram Gateway & Interactive Channel enabling tri-agent dispatch, cross-model consensus discussion, and subagent supervision from mobile.

## 2026-08-19 23:05 [saved]
Goal: Audit achiAgy with Claude Opus and apply critical reliability & UX fixes via TDD.

Decisions:
- Dispatched dual Claude Opus 4.6 (Thinking) subagents to audit systems reliability and Telegram UX.
- Fixed `session_manager.py` token metrics: stopped sliding-context accumulation (fixed bogus 1.65B token metric), added `peak_context_tokens` tracking, and prevented double turn-counting via `set_conversation_id()`.
- Added rich `MODEL_REGISTRY` in `config.py` with exact token context and output bounds.
- Added native Telegram autocomplete menu (`set_my_commands` in `post_init`) with 15 direct commands.
- Implemented proactive context health alerts at ≥75% (warning) and ≥90% (critical).
- Added stripped plaintext fallback on Telegram HTML `BadRequest` errors.
## 2026-08-19 23:12 [saved]
Goal: Audit TGDB vault archive, correction harvester, and self-learning loop (`docs/2026-08-18-feature-audit-tgdb-and-correction-harvester.md`).

Decisions:
- Audited `scripts/extract_corrections.py`, `scripts/export_transcripts.py`, `scripts/vault_inbox_sync.py`, and `scripts/evening_debrief.py`.
- Identified root cause of broken self-learning loop: overly permissive regex (`take note`, `make sure`, `change X to Y`) ingesting conversational task requests and file edit instructions as permanent `.agentrules`.
- Identified transcript exporter gaps: missing OpenAI keys in secret redactor, missing `<thought>`/`<thinking>` and case-insensitive tags in Claude cleaner, and trailing uncommitted AIS-OS changes in `vault_inbox_sync.py`.
- Cleaned up `.agentrules` and `decisions/log.md` to remove polluted conversational task entries.
- Formalized AI Model Allocation rule: Claude Opus for auditing and feature plan drafting; Gemini 3.7 Flash for execution, tool runs, and code implementation.
- Audited NousResearch Hermes Agent self-learning loop (`agent/learn_prompt.py`, `learning_graph.py`, `learning_mutations.py`, `memory_tool.py`).
- Produced Superpowers-grade implementation plan (`docs/superpowers/plans/2026-08-19-self-learning-loop-implementation.md`) detailing the dual-track memory/skill architecture, budget compaction, `/learn` authoring engine, and test suites ready for Gemini 3.7 Flash execution.
## 2026-08-20 08:42 [saved]
Goal: Merge self-learning engine into main/master, fix model stream error handling, and implement live Antigravity Models & Quota in /usage.

Decisions:
- Merged all self-learning loop and TGDB features into `main` (`AIS-OS`) and `master` (`achiAgy`); verified all 29 tests in `achiAgy` and 61 tests in `AIS-OS`.
- Fixed Antigravity CLI event streaming in `src/agy_client.py` and `src/bot.py` to capture and surface backend error events (e.g. Opus 5-hour quota exhaustion) rather than silently completing.
- Built live Antigravity backend quota connector in `src/quota.py`, querying `https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary` and Google OAuth userinfo.
- Redesigned `/usage` command output to display live progress bars, exact percentages, and relative refresh countdowns formatted as `Xd Xh Xm` across Gemini and Claude/GPT model groups.
- Marked Hermes Self-Learning Loop implementation and TGDB architecture audit done in `tasks.md`.
- Restarted `achi-agy.service` and confirmed live Telegram operation.
