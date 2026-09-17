# Asta and calendar discussion, September 16 to 17, 2026

Aki and Claude Code grilled three research documents into an Asta plan, tested the persona live three times, then opened a second discussion on Google Calendar after Asta could not read Aki's schedule. This record keeps the decisions and their reasons. The implementation tickets and ordering live in the [roadmap](asta-calendar-roadmap-2026-09-17.md).

The research documents stay private in `~/Documents/Files/training/`:
`asta_health_agent_research_discussion_v3.md`, `asta_ai_calorie_tracking_deep_research.md` and `asta_foundational_system_prompt_research.md`.

## Server facts that shaped the plan

- Bound turns run under Landlock. `~/.local/share` is always protected because the timer venv lives there, so Asta's database sits under `~/.local/state`.
- `gemini-3.8-flash` is registered on agy and is the default model.
- Photos reach a turn as a path in the hub's attachments directory, with no retention.
- There is no scheduler inside the daemon. Timers run AIS-OS scripts, and `telegram_notify.send()` cannot target a forum topic.
- No SQLite database on the server had backups.
- `gcal_add.py` only inserts all-day events. Five scripts carry their own copy of the gws wrapper, and three instruction files disagree about calendar placement.
- `cohesion.py` exists only in PR #59.

## Asta decisions

### Scope and order

- Full tickets for the `asta.py` foundation, nutrition, workout scheduling and Apple Health ingest. Tracking issues only for second-wave nutrition, a weighed benchmark, manual lifting logs, Fitbit and Hevy. Why: Hevy's API is at 0.0.1 and Aki has no Fitbit yet, so detailed tickets would go stale.
- Order is foundation, nutrition, calendar scheduling, then Apple ingest. Why: sessions can be scheduled before workout data exists.
- MVP acceptance: onboarding sets targets, text and photo meals land with ranges and provenance, and a 21:00 Manila summary posts in the Asta topic. Aki mostly photographs real food, rarely barcodes.

### Placement and privacy

- Code follows the Canvas split. AIS-OS owns `asta.py`, adapters, timers and the listener. achiCore owns the persona, topic and `/mealcheck`.
- Database at `~/.local/state/achios/asta/asta.sqlite3`, written only by `asta.py`. Why: no Landlock exception and no daemon intent path.
- Workspace, meal photos and backups under `~/Documents/Files/training/asta/`. Aki accepted that the unauthenticated file viewer serves this folder.
- Photos are moved from attachments, named by hash and kept indefinitely with no second copy.
- Nightly SQLite backups keep 14 copies, unencrypted.
- Nothing crosses into achiMem.

### Nutrition

- The model estimates grams. Food records supply nutrients. The CLI does all arithmetic. Why: the calorie research names a single model calorie number as the main anti-pattern.
- Resolution order: personal templates, a private hand-copied PhilFCT staples seed, USDA FoodData Central behind a cache. A model density estimate is the last resort and always flags. Open Food Facts waits for the second wave.
- Confidence is stored per item as identity, portion, source and hidden-ingredient risk. The CLI computes the tier from the kcal range, with thresholds in config.
- Three tiers from day one: commit, commit and flag, ask one question. `needs_answer` saves nothing.
- Corrections append rows and never overwrite the original estimate. Why: correction data is the input to later calibration.
- Estimates show point, range and confidence. Flagged meals count toward totals.
- Provenance on every AI-derived record: model, effort, prompt version, schema version and image hash.
- Aki owns a kitchen scale, so the benchmark tracking issue uses a weighed subset.

### Targets and onboarding

- Mifflin-St Jeor times an activity factor, a goal adjustment, 1.8 g/kg protein and at least 0.8 g/kg fat, computed by `targets suggest`, never in the prompt. Aki approves or overrides.
- Onboarding is conversational, grouped and skippable. Profile rows are versioned.
- Body weight logging and a 7-day average are in the MVP.

### Persona

- `agents/asta.md` keeps the researched foundation prompt and adds an architecture extension naming the CLI contract. Merged in achiCore PR #220 at prompt `asta-0.1.3`.
- Mixins are `topic-isolation` and `communication` only, so health data cannot be delegated.
- While a tool is missing, Asta says so once per conversation. It may give a labeled meal estimate with a confidence word, and provisional targets with a 0 to 100 percent confidence. Nothing is described as saved or set.
- Telegram replies use no bold, italics or headings. Asta mentions no split, schedule or target a tool did not return, names no specific injury, and cites only sources `search_web` returned that turn.
- Reading any of Aki's calendars to plan training is Asta's job.
- A 34-scenario eval fixture is traced to prompt text by tests.

### Live eval passes

| Pass | Prompt | Result | Main findings |
|---|---|---|---|
| 1 | 0.1.0 | 7 of 11 clean | Decorative bold, silent failed status call, named pulley diagnosis, unretrieved citation, invented history |
| 2 | 0.1.1 | 10 of 15 clean | Assumed routines, ignored calendar request, targets computed in-head |
| 3 | 0.1.2 | Targets passed | Asta refused to read the school calendar as another topic's |

Aki's onboarding answers from pass 2 are saved privately in `~/Documents/Files/training/asta/onboarding-draft.md` for import.

## Calendar decisions

- Every persona may read Aki's calendars. Only Asa, Asta and the cohesion writer write, each to calendars it owns. Why: reading is harmless and every planning agent needs it; ownership stops one agent moving another's events.
- Write owners: Asta writes `workouts`. Course, DLSU and thesis calendars follow #13's routing. Asa writes Personal. GCash and Job are read-only for agents. Imported and free/busy calendars are read-only.
- Two layers. `gcal.py` is the only code that talks to Google. The cohesion writer from #13 builds on it, and simple agents call it directly for their own calendars.
- One configured set of schedule calendars, deduplicated by calendar and event ID, with the profile chosen per calendar. The set is current course calendars, DLSU, Personal, workouts, ING, LSCS, Family, Holidays in Philippines and the Canvas import. GCash, Bdayy, Job, past course calendars and the free/busy DLSU view are out.
- Confirmation: a single explicit event writes without asking. Several events, moves and deletes confirm once. Agents never touch events they do not own or read-only calendars.
- Every created event carries `achios_owner` and `achios_item_id`. Why: one guard in one place, compatible with the key cohesion already uses.
- Placement follows whatever #13 settles when PR #59 lands. The three instruction files are corrected afterwards.
- Routing moves from prose to a private `~/.config/achios/calendars.json`, with a committed example and a `calendars check` drift command that also compares against current Canvas courses. Calendars are never created automatically.
- PR #59 finishes first. A follow-up moves cohesion onto the shared client.
- `gcal_add.py` and its tests are deleted after callers move, with no compatibility wrapper.
- The briefs, auth health check and email digest move onto the shared client with one dedupe rule.
- The three unused `google_token*.json` files are deleted, with a test that fails if one exists.

## Superseded during the discussion

- Meal photos under `personal/health` with a viewer block rule, replaced by `training/asta`.
- MVP nutrition without USDA, replaced after the calorie research.
- Target constants in the persona, moved to `asta.py`.
- A per-agent `asta_id` event key, replaced by `achios_owner`.
- A quick read-only `gcal.py agenda` shortcut, dropped in favour of the universal client ticket.
