# Unified AIS-OS open tickets implementation plan

> **For the implementer:** Execute this plan in one model session. Do not delegate to subagents. Keep the current viewer branches and their working trees untouched.

**Goal:** Deliver AIS-OS issues [#3](https://github.com/achibukz/AIS-OS/issues/3), [#5](https://github.com/achibukz/AIS-OS/issues/5), [#6](https://github.com/achibukz/AIS-OS/issues/6), [#7](https://github.com/achibukz/AIS-OS/issues/7), and [#8](https://github.com/achibukz/AIS-OS/issues/8), plus [achiCore #57](https://github.com/achibukz/achiCore/issues/57), as one coordinated release.

**Architecture:** Add one pure task engine and one shared `gws` client in AIS-OS. Every task consumer uses the task engine. Every Google consumer uses the `gws` client. AIS-OS ships first, then achiCore consumes the new task API in the same release window.

**Tech stack:** Python 3.13, pytest, Google Workspace CLI, systemd user units, Telegram Bot API, Gemini through `agy`, GitHub pull requests.

---

## Locked decisions

The grill completed on 2026-09-03. These choices are final for this plan.

1. Include the five open AIS-OS issues and achiCore #57.
2. Preserve the current one-message chronological daily brief introduced by commit `feff6f1`. Do not restore the older two-message layout.
3. Move the `achiclaude` OAuth consent screen from Testing to Production. Keep health monitoring because refresh tokens can still be revoked, but remove the seven-day age warning and weekly reauthentication instructions.
4. Add `scripts/gws_client.py` and `scripts/task_engine.py` instead of patching each consumer independently.
5. Run a silent daily Google health check and send one positive Sunday heartbeat.
6. Use clean implementation worktrees. Open one AIS-OS integration pull request and one dependent achiCore pull request.
7. Update the stale Google-auth text in [CLAUDE.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/CLAUDE.md). This is the narrow exception authorized by Aki to the Claude-only file rule.
8. Render fixed deadline sections first. Use cached semantic groups for undated tasks. Fall back to deterministic `#area` groups when Gemini fails or returns invalid data.
9. Keep the existing issues as acceptance records. The AIS-OS pull request closes all five AIS-OS issues. The achiCore pull request closes #57.
10. Deploy in one controlled release window. AIS-OS goes first, followed by achiCore.
11. Preserve the August 29 plan as history and mark it superseded.
12. Replace the ticket's ineffective calendar `--dry-run` write probe. Prove write capability with a live calendar read, the full Calendar OAuth scope from `gws auth status`, and an `owner` or `writer` access role from `calendarList.list`.

## Current baseline

- AIS-OS is currently on `feat/viewer-secrets-toggle` at `f36c083`. The working tree is clean.
- achiCore is currently on `feat/viewer-secrets-toggle` at `98ffa7a`. Its [session-log.md](http://100.106.210.38:8999/Code/GitHub/achiCore/session-log.md) has an unrelated modification.
- Do not implement on either working tree.
- AIS-OS has no open pull requests.
- AIS-OS tests currently report `44 failed, 278 passed`. Every failure is in `tests/test_daily_brief.py`.
- `tests/test_gcal_add.py` reports `21 passed`. Issue #4 is complete and stays closed.
- achiCore reports `649 passed, 21 subtests passed`.
- All four `gws` profiles currently pass live Calendar reads. `personal`, `work`, and `dlsu` also pass Gmail reads.
- Their credentials were refreshed on 2026-08-28. The August 29 ticket evidence says the consent screen was in Testing, while the August 10 decision log says it had already been published. The release must verify the live Google Cloud setting and leave it in Production.
- `scripts/evening_debrief.py` still contains the legacy direct-token path even though issue #7 names only the daily and email digests.

## Target design

```text
master task register
   |
   v
task_engine.py --------------------+
   |                               |
   v                               v
tasks_digest.py              achiCore /tasks

gws profiles
   |
   v
gws_client.py ---------------------+--------------------+
   |                |              |                    |
   v                v              v                    v
gcal_add.py   daily_brief.py  email_digest.py  evening_debrief.py
                       |
                       v
             google_auth_health.py
                       |
                       v
            daily alert + Sunday heartbeat
```

### Task engine contract

Create `scripts/task_engine.py` with no Telegram imports and no work at import time.

```python
@dataclass(frozen=True)
class Task:
    text: str
    state: str
    priority: str
    due: date | None
    areas: tuple[str, ...]
    source_index: int


def parse_tasks(content: str) -> list[Task]: ...


def build_task_card(
    content: str,
    *,
    today: date,
    classifier: SemanticClassifier | None = None,
    cache_path: Path | None = None,
) -> TaskCard: ...


def render_task_card(card: TaskCard, *, html: bool = False) -> str: ...
```

The engine must enforce these rules:

- Parse `## Active` and `## Blocked`; ignore examples inside fenced code blocks.
- Preserve every active task exactly once.
- Put dated work into `Overdue`, `Due today`, or `Upcoming`. There is no 30-day cutoff and no item cap.
- Put blocked work last.
- Show priority and date together when both exist.
- Default a missing priority to `med`.
- Strip raw hashtags from display text.
- Preserve clickable links to Markdown files through the Tailscale viewer.
- Give undated tasks stable internal IDs. Ask Gemini only for an ID-to-category mapping.
- Validate that the mapping contains every undated ID exactly once and invents no IDs.
- Cache valid semantic mappings under `~/.local/state/achios/tasks_renderer_cache.json`, keyed by a SHA-256 digest of canonical undated task records.
- On a cache hit, make no model call. Unchanged task input must produce byte-identical output.
- On timeout, model failure, or invalid output, group undated tasks by their first `#area`, with `Other` as the final fallback.
- Render Telegram-safe HTML for the scheduled digest and achiCore. Keep a plain-text form for `--dry-run` and tests.

The Gemini classifier uses `gemini-3.7-flash-high` through an isolated `agy -p` call. It does not enter or increment an achiCore conversation.

### Google client contract

Create `scripts/gws_client.py` as the only source for profile names, environment variables, subprocess execution, JSON cleanup, and error normalization.

```python
PROFILES = ("personal", "work", "main", "dlsu")
GMAIL_PROFILES = frozenset({"personal", "work", "dlsu"})
WRITABLE_ROLES = frozenset({"owner", "writer"})


class GwsError(RuntimeError): ...


def run_gws(profile: str, *args: str, timeout: int = 30) -> dict: ...
def auth_status(profile: str) -> dict: ...
def calendar_access(profile: str) -> list[dict]: ...
```

Every subprocess must set both variables:

```text
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-<profile>
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file
```

Do not retain the current `KEYRING_BACKEND=file` spelling. The CLI documents only `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND`.

### Health definition

A profile is healthy only when all required checks pass:

1. `gws auth status` reports encrypted credentials, a refresh token, and `https://www.googleapis.com/auth/calendar`.
2. `gws calendar +agenda --days 1` succeeds against Google.
3. `gws calendar calendarList list` succeeds and returns at least one calendar with `accessRole` equal to `owner` or `writer`.
4. Profiles in `GMAIL_PROFILES` pass `gws gmail users messages list --params '{"userId":"me","maxResults":1}'`.

The third check is the read-only proof of calendar write authorization. `gws events insert --dry-run` is excluded because it validates locally and never tests the credential.

`scripts/google_auth_health.py` owns the `ProfileStatus` model, profile probing, dead-profile naming, message construction, and CLI behavior. Digest modules import this definition rather than duplicating it.

### Timer design

Use separate units because one systemd timer cannot pass different arguments for its two trigger times.

- `systemd/achios-google-auth-health.service` runs the default command.
- `systemd/achios-google-auth-health.timer` runs daily at `07:30 Asia/Manila`.
- `systemd/achios-google-auth-heartbeat.service` runs with `--weekly`.
- `systemd/achios-google-auth-heartbeat.timer` runs Sunday at `09:00 Asia/Manila`.

Both timers use `Persistent=true` and `AccuracySec=1min`. Both services use the shared failure-alert unit, a five-minute timeout, `Restart=on-failure`, and the standard `~/.local/share/achios/venv/bin/python` interpreter.

The default command sends only when a profile is unhealthy. `--weekly` always sends one compact status message. `--dry-run` prints all four profiles and never sends. A detected auth failure exits zero after its warning sends successfully. Script failures and notification failures exit nonzero.

## Implementation sequence

### Task 1: Create clean implementation worktrees

**Objective:** Isolate the batch from both viewer branches.

**Commands:**

```bash
git -C /home/achibukz/Code/GitHub/AIS-OS fetch origin
git -C /home/achibukz/Code/GitHub/AIS-OS worktree add \
  -b codex/unified-open-tickets \
  /home/achibukz/Code/GitHub/AIS-OS-unified-open-tickets origin/main

git -C /home/achibukz/Code/GitHub/achiCore fetch origin
git -C /home/achibukz/Code/GitHub/achiCore worktree add \
  -b ticket/57-shared-task-renderer \
  /home/achibukz/Code/GitHub/achiCore-ticket-57 origin/master
```

**Verification:** The original AIS-OS and achiCore worktrees remain on `feat/viewer-secrets-toggle`. Their status output does not change.

### Task 2: Record the revised ticket contracts

**Objective:** Make the approved batch semantics visible before code changes begin.

**External records:**

- Comment on AIS-OS #3 that the chronological one-message brief is the source of truth.
- Comment on AIS-OS #5 that Production OAuth removes the age warning and weekly reauthentication commands.
- Comment on AIS-OS #5 that `--dry-run` cannot prove write access and name the read-only replacement.
- Comment on AIS-OS #6 with the cached semantic grouping and deterministic fallback rules.
- Comment on AIS-OS #7 that removal includes `scripts/evening_debrief.py` and the authorized [CLAUDE.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/CLAUDE.md) correction.
- Comment on AIS-OS #8 that both digests use the shared health definition.
- Comment on achiCore #57 with the dependency on the new `task_engine.py` API.

Do not close or relabel any issue at this stage.

### Task 3: Repair the daily brief regression net

**Objective:** Finish #3 without restoring the obsolete layout.

**Files:**

- Modify: `tests/test_daily_brief.py`
- Do not modify yet: `scripts/daily_brief.py`

**Steps:**

1. Replace tests for removed names such as `schedule_message`, `tasks_message`, `color_dot`, and `polish_with_claude`.
2. Add fixed-date fixtures around `CalendarEvent`, `Task`, and `build_daily_brief`.
3. Assert chronological timed events, all-day placement, five-action cap, overdue inclusion, upcoming ordering, and current empty-state wording.
4. Assert the current one-message structure exactly through a representative multiline snapshot.
5. Run `~/.local/share/achios/venv/bin/python -m pytest tests/test_daily_brief.py -q`.
6. Expect zero failures without production-code changes.
7. Commit as `test(daily-brief): align coverage with chronological format`.

### Task 4: Build the pure task engine with TDD

**Objective:** Create the shared parser, lossless bucketing, semantic cache, and fallback.

**Files:**

- Create: `scripts/task_engine.py`
- Create: `tests/test_task_engine.py`

**Test order:**

1. Parse active, blocked, done, priority, date, multiple areas, Markdown links, and fenced examples.
2. Verify that a far-future task remains visible.
3. Verify that a dated `!high` task shows both fields.
4. Verify that rendered task IDs equal parsed active task IDs with no duplicates.
5. Verify deadline sections in the order `Overdue`, `Due today`, `Upcoming`.
6. Verify blocked tasks appear last and completed tasks do not appear.
7. Verify valid semantic classifier output groups every undated task.
8. Verify a cache hit makes no classifier call and returns byte-identical output.
9. Verify missing IDs, duplicate IDs, invented IDs, malformed JSON, timeouts, and subprocess failures all use the deterministic area fallback.
10. Verify plain-text and HTML renderers preserve the same item order.

Run each new test first and confirm that it fails for the intended missing behavior. Implement only enough code to pass that test before moving on.

**Verification:**

```bash
~/.local/share/achios/venv/bin/python -m pytest tests/test_task_engine.py -q
```

**Commit:** `feat(tasks): add shared lossless task engine`

### Task 5: Move the scheduled task digest onto the engine

**Objective:** Finish AIS-OS #6 for the cron path without changing Telegram's default behavior for other jobs.

**Files:**

- Modify: `scripts/tasks_digest.py`
- Modify: `scripts/telegram_notify.py`
- Create: `tests/test_tasks_digest.py`
- Modify: `tests/test_telegram_notify.py`

**Steps:**

1. Add failing adapter tests showing `tasks_digest.py` imports the engine and does not retain its own parser or bucket logic.
2. Add an optional Telegram `parse_mode` argument. Keep the default request body byte-equivalent for all existing callers.
3. Make `tasks_digest.py --dry-run` render plain text and send nothing.
4. Make the live path send the HTML form.
5. Assert a far-future task, dated high-priority task, blocked task, default priority, empty register, and exact parsed-to-rendered count.
6. Run the focused tests.

**Verification:**

```bash
~/.local/share/achios/venv/bin/python -m pytest \
  tests/test_task_engine.py \
  tests/test_tasks_digest.py \
  tests/test_telegram_notify.py -q
python scripts/tasks_digest.py --dry-run
```

**Commit:** `refactor(tasks): use shared renderer without dropping work`

### Task 6: Add the shared Google Workspace client

**Objective:** Put profile selection and subprocess behavior in one tested module.

**Files:**

- Create: `scripts/gws_client.py`
- Create: `tests/test_gws_client.py`
- Modify: `scripts/gcal_add.py`
- Modify: `tests/test_gcal_add.py`

**Steps:**

1. Test the missing-binary error and require the exact binary path in the message.
2. Test both required environment variables for every subprocess.
3. Test removal of the CLI's keyring banner before JSON parsing.
4. Test nonzero exit normalization, timeout propagation, and invalid JSON.
5. Move profile constants, `run_gws`, profile directory resolution, and writable-role rules into the client.
6. Refactor `gcal_add.py` without changing its existing behavior.
7. Re-run the 21 existing calendar tests and the new client tests.

**Verification:**

```bash
~/.local/share/achios/venv/bin/python -m pytest \
  tests/test_gws_client.py tests/test_gcal_add.py -q
python scripts/gcal_add.py --list
```

**Commit:** `refactor(google): centralize gws profile access`

### Task 7: Build Google auth health checks and timers

**Objective:** Finish the revised #5 contract.

**Files:**

- Create: `scripts/google_auth_health.py`
- Create: `tests/test_google_auth_health.py`
- Create: `systemd/achios-google-auth-health.service`
- Create: `systemd/achios-google-auth-health.timer`
- Create: `systemd/achios-google-auth-heartbeat.service`
- Create: `systemd/achios-google-auth-heartbeat.timer`
- Modify: `scripts/install_units.sh` only if its existing glob installation cannot install the four units unchanged

**Test order:**

1. Healthy profile with Calendar scope, live Calendar response, writable role, and Gmail response where required.
2. Missing refresh token.
3. Missing Calendar scope.
4. Calendar read failure.
5. No writable calendar role.
6. Gmail read failure.
7. One dead profile named with its failed checks.
8. Several dead profiles named once each.
9. Default healthy run produces no message.
10. `--weekly` produces one message for an all-healthy result.
11. `--dry-run` prints all four profiles and never calls `send`.
12. Unit-file assertions for timezone, persistence, failure alert, restart policy, interpreter, and `--weekly` separation.

**Verification:**

```bash
~/.local/share/achios/venv/bin/python -m pytest tests/test_google_auth_health.py -q
python scripts/google_auth_health.py --dry-run
systemd-analyze --user verify \
  systemd/achios-google-auth-health.service \
  systemd/achios-google-auth-health.timer \
  systemd/achios-google-auth-heartbeat.service \
  systemd/achios-google-auth-heartbeat.timer
```

Do not install or start the units during implementation. Installation belongs to the release procedure.

**Commit:** `feat(google): add auth health check and heartbeat`

### Task 8: Remove every legacy Google token path

**Objective:** Finish #7 across all actual consumers after the shared client and health checker are green.

**Files:**

- Modify: `scripts/daily_brief.py`
- Modify: `scripts/email_digest.py`
- Modify: `scripts/evening_debrief.py`
- Delete: `scripts/auth_google_account.py`
- Modify: `tests/test_daily_brief.py`
- Modify: `tests/test_email_digest.py`
- Modify: `tests/test_evening_debrief.py`
- Modify: [AGENTS.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/AGENTS.md)
- Modify: [CLAUDE.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/CLAUDE.md), Google-auth references only
- Modify other current documentation that instructs the operator to run `auth_google_account.py`

**Steps:**

1. Add tests that make `GWS_BIN` unavailable and expect a hard error naming the path.
2. Add tests proving no consumer opens a legacy token file.
3. Replace each local `gws` runner with `gws_client.py` calls.
4. Remove `GOOGLE_TOKENS`, account `tokens` entries, Google client-library imports, and direct refresh branches.
5. Delete `scripts/auth_google_account.py`.
6. Update current operational documentation. Historical audit and design documents may retain references when they clearly describe past state.
7. Do not delete the three runtime token files yet. That happens only after the Production OAuth cutover passes.

**Verification:**

```bash
rg -n "google_token|auth_google_account" scripts tests AGENTS.md CLAUDE.md
rg -n "google\.oauth2|googleapiclient|google\.auth" scripts
~/.local/share/achios/venv/bin/python -m pytest \
  tests/test_daily_brief.py \
  tests/test_email_digest.py \
  tests/test_evening_debrief.py \
  tests/test_gcal_add.py \
  tests/test_gws_client.py \
  tests/test_google_auth_health.py -q
```

The first search may return historical documentation outside the searched paths. It must return nothing in live scripts and current operating instructions.

**Commit:** `refactor(google): remove legacy OAuth token path`

### Task 9: Add dead-profile banners to the digests

**Objective:** Finish #8 without suppressing non-Google content.

**Files:**

- Modify: `scripts/google_auth_health.py`
- Modify: `scripts/daily_brief.py`
- Modify: `scripts/email_digest.py`
- Modify: `tests/test_google_auth_health.py`
- Modify: `tests/test_daily_brief.py`
- Modify: `tests/test_email_digest.py`

**Steps:**

1. Expose one pure `dead_profile_names` function from `google_auth_health.py`.
2. Inject health results into both digest builders so tests never call Google.
3. Add one banner above the first section when any profile is dead.
4. Keep healthy output byte-identical to the Task 3 snapshot.
5. Name one or several dead profiles on one line.
6. Keep sending the task portion of the daily brief and all healthy email-account sections.
7. Preserve the existing chronological layout below the banner.

**Verification:**

```bash
~/.local/share/achios/venv/bin/python -m pytest \
  tests/test_google_auth_health.py \
  tests/test_daily_brief.py \
  tests/test_email_digest.py -q
```

**Commit:** `feat(digests): report dead gws profiles`

### Task 10: Integrate achiCore `/tasks` and clean `/status`

**Objective:** Finish achiCore #57 after the AIS-OS API is stable.

**Files in `/home/achibukz/Code/GitHub/achiCore-ticket-57`:**

- Modify: `src/bot.py`
- Modify: `tests/test_bot_routing.py`
- Modify or create a focused command test file if `tests/test_bot_routing.py` becomes harder to read

**Steps:**

1. Add a failing test that invokes `/tasks` three times with unchanged [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) content and compares exact replies.
2. Assert that `/tasks` does not call `_start_session_turn` and does not change the session turn count.
3. Assert that the reply stays in the originating Telegram topic.
4. Import the shared task engine through the existing AIS-OS scripts path.
5. Run cache misses through `asyncio.to_thread` so the Telegram event loop remains responsive during the dedicated classifier call.
6. Reply with the engine's Telegram-safe HTML.
7. Replace `/status` with the flat label-and-value list from issue #57.
8. Assert that `/status` contains every existing field, contains no emoji codepoints, contains no `<b>` tag, and omits the old title.

**Verification:**

```bash
cd /home/achibukz/Code/GitHub/achiCore-ticket-57
.venv/bin/python -m pytest tests/test_bot_routing.py -q
.venv/bin/python -m pytest -q
```

**Commit:** `feat(commands): make tasks deterministic and simplify status`

### Task 11: Run the complete regression gates

**Objective:** Prove the batch is ready before either pull request opens.

**AIS-OS verification:**

```bash
cd /home/achibukz/Code/GitHub/AIS-OS-unified-open-tickets
~/.local/share/achios/venv/bin/python -m pytest tests/ -q
python scripts/daily_brief.py --dry-run
python scripts/email_digest.py --dry-run
python scripts/evening_debrief.py --dry-run
python scripts/tasks_digest.py --dry-run
python scripts/google_auth_health.py --dry-run
python scripts/gcal_add.py --list
```

Expected automated result: zero failed tests. Dry runs send no Telegram messages and create no calendar events.

**achiCore verification:**

```bash
cd /home/achibukz/Code/GitHub/achiCore-ticket-57
.venv/bin/python -m pytest -q
```

Expected automated result: at least the current `649 passed, 21 subtests passed`, plus the new command tests.

### Task 12: Update operational records

**Objective:** Leave the repositories accurate after implementation.

**AIS-OS files:**

- [AGENTS.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/AGENTS.md)
- [CLAUDE.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/CLAUDE.md), within the authorized scope
- [connections.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/connections.md)
- [decisions/log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/decisions/log.md)
- [session-log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/session-log.md)
- [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md)
- [docs/tasks-systems-engineering.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/tasks-systems-engineering.md)

**achiCore files:**

- [session-log.md](http://100.106.210.38:8999/Code/GitHub/achiCore/session-log.md)
- Update the [roadmap.md](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/roadmap.md) only if #57 changes a recorded dependency or deployment status.

Record exact tests, dry runs, live checks, deployment state, decisions, rejected approaches, and open operator actions. Move completed task-register entries to `## Done`; do not delete them.

**Commit:** `docs: record unified ticket release`

### Task 13: Open the linked pull requests

**Objective:** Review the batch as one release without losing issue-level traceability.

**AIS-OS pull request:**

- Base: `main`
- Head: `codex/unified-open-tickets`
- Include `Closes #3`, `Closes #5`, `Closes #6`, `Closes #7`, and `Closes #8`.
- Explain every approved departure from the original issue bodies.
- Include exact test counts and dry-run results.
- Do not merge until all checks pass.

**achiCore pull request:**

- Base: `master`
- Head: `ticket/57-shared-task-renderer`
- Include `Closes #57`.
- State that deployment requires the AIS-OS task engine first.
- Follow achiCore's required reviewer mention and identity rules.
- Do not merge until its full suite and CI pass.

### Task 14: Perform the controlled release

**Objective:** Cut over OAuth and deploy both repositories without a period where achiCore imports a missing module.

**Manual Google gate:**

1. Inspect the live `achiclaude` OAuth publishing status in Google Cloud Console. Change it to Production if it is in Testing.
2. Reauthorize `personal`, `work`, `main`, and `dlsu` once through `gws auth login` with Gmail and Calendar services.
3. Confirm `gws auth status` for all four profiles reports the Calendar scope and encrypted credentials.
4. Run the live Calendar and Gmail read checks used by `google_auth_health.py`.
5. Stop if Google or the DLSU administrator blocks any required scope. Do not delete fallback files or deploy consumers while a required profile is unhealthy.

**AIS-OS deployment:**

1. Merge and fast-forward AIS-OS first.
2. Run `scripts/install_units.sh` from the deployed checkout.
3. Run every dry-run command from Task 11.
4. Start `achios-google-auth-health.service` manually and inspect `~/.local/state/achios/google_auth_health.log`.
5. Verify both new timers with `systemctl --user list-timers 'achios-google-auth-*' --no-pager`.
6. Run `systemctl --user start achios-daily-brief.service`, `achios-email-digest.service`, and `achios-evening-debrief.service` only after dry runs pass. These commands send live messages, so execute them once.

**achiCore deployment:**

1. Merge and fast-forward achiCore only after the AIS-OS task engine exists in the deployed checkout.
2. Restart `achicore-hub.service` through its repository-approved control path.
3. Invoke `/tasks` three times with unchanged input. Compare the replies byte for byte and confirm the session turn count does not move.
4. Invoke `/status` and confirm every field remains while emoji, bold labels, and the old title are absent.

**Legacy runtime cleanup:**

Delete only these explicit files after the Production credentials and deployed consumers pass:

```text
/home/achibukz/.config/achios/google_token.json
/home/achibukz/.config/achios/google_token_dlsu.json
/home/achibukz/.config/achios/google_token_work.json
```

Do not use a glob. Record whether each file existed and whether recovery would require a new OAuth login.

## Rollback

Rollback follows dependency order in reverse.

1. Revert achiCore #57 and restart the hub.
2. Disable the two new auth timers if the health checker is the failure source.
3. Revert the AIS-OS integration pull request.
4. Re-run `scripts/install_units.sh` from the reverted checkout.
5. Restore legacy token files only from a known secure backup and only if they remain valid. Do not treat dead tokens as a recovery path.
6. Moving the consent screen back to Testing is not required for code rollback. It would reintroduce the seven-day expiry and should need a new decision.

## Completion checklist

- [ ] AIS-OS full suite passes.
- [ ] achiCore full suite passes.
- [ ] Current daily brief output is protected by tests.
- [ ] Every active task renders exactly once.
- [ ] Unchanged tasks produce byte-identical `/tasks` replies.
- [ ] Semantic grouping falls back without losing tasks.
- [ ] Every Google consumer uses `gws_client.py`.
- [ ] No live script or current operating instruction references legacy token files.
- [ ] All four Production OAuth profiles pass live checks.
- [ ] Daily health silence and Sunday heartbeat are verified.
- [ ] Dead-profile banners preserve all non-Google digest content.
- [ ] AIS-OS deploys before achiCore.
- [ ] AIS-OS issues #3, #5, #6, #7, and #8 close through one pull request.
- [ ] achiCore #57 closes through its linked pull request.
- [ ] Logs, task state, connections, and operating instructions match the deployed result.

## Risks and controls

- **Google verification or DLSU policy blocks Production scopes.** Stop at the manual gate. Keep the current `gws` profiles and do not remove runtime fallback files until a new decision is made.
- **The semantic classifier loses or duplicates tasks.** Validate IDs as an exact set before accepting output. Fall back to deterministic grouping on any mismatch.
- **The task cache becomes corrupt.** Treat it as a cache miss and replace it atomically after the next valid classification.
- **A digest changes while #3 is being repaired.** Capture the current chronological output before refactoring and keep the healthy-output test byte exact.
- **achiCore deploys before AIS-OS.** Keep the PR dependency explicit and deploy AIS-OS first.
- **The broad Google refactor breaks a quiet path.** Run focused tests after each commit and both full suites before opening pull requests.
- **The current viewer work is overwritten or mixed into the batch.** Use the two dedicated worktrees and never switch branches in the existing working directories.

## No implementation in this plan commit

This document authorizes and sequences later work. It does not create modules, change services, publish OAuth, delete credentials, modify tickets, open pull requests, or deploy anything.
