# Tasks view filtering, backlog support, and command options, September 11, 2026

Approved planning decisions from the discussion with Aki. This records requested behavior, not a claim that the features have shipped. The published issue is tracked in [the roadmap](astra-roadmap-2026-09-11.md).

## What Aki wants

The task register accumulated numerous systems tickets, engineering maintenance chores, and project research items. When Aki runs `/tasks` with no parameters, these system and ticket tasks bloat the list, obscuring immediate academic, personal, and career priorities.

Aki wants:
1. Default `/tasks` (no arguments) to exclude `#systems`, tickets and issues (`#<id>` and issue links), engineering maintenance, and non-school project research.
2. `/tasks all` (`--area all`) to display the full register without filtering, including systems, tickets, and engineering tasks.
3. `/tasks backlog` or `/tasks backlogs` (`--area backlog`) to inspect deferred items stored in `## Backlog`.
4. Specific area filters (`/tasks school`, `/tasks personal`, `/tasks career`, `/tasks projects`, `/tasks systems`, `/tasks uncategorized`) to remain available. Explicitly running `/tasks systems` shows systems tasks.
5. Scheduled briefs and crons (`daily_brief.py`, `tasks_digest.py`) to continue excluding `## Backlog` so deferred items do not pollute scheduled Telegram notifications.
6. Native Telegram handling in achiCore without model turns (`achiCore #57`) to forward arguments properly rather than dropping parameters.

## Architectural boundaries

- `scripts/task_engine.py` in `achibukz/AIS-OS` is the deterministic source of truth for parsing and rendering `tasks.md`.
- `parse_tasks()` parses `## Backlog` entries with `state="backlog"`.
- `render_tasks()` implements the default exclusion rules when `area is None`, and supports `area="all"` and `area="backlog"`.
- `scripts/tasks_digest.py` accepts `--area all` and `--area backlog` in addition to primary areas.
- `achibukz/achiCore#57` updates `cmd_tasks` in `src/bot.py` to forward arguments directly to `task_engine.py` without spending agent turns.
