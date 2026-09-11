# Canvas client, cache and notifications

This implements the source work for [#26](https://github.com/achibukz/AIS-OS/issues/26), [#28](https://github.com/achibukz/AIS-OS/issues/28) and [#29](https://github.com/achibukz/AIS-OS/issues/29). Phone login is [#27](https://github.com/achibukz/AIS-OS/issues/27) and hub integration is [achiCore #173](https://github.com/achibukz/achiCore/issues/173). The 30-minute timer from [#30](https://github.com/achibukz/AIS-OS/issues/30) is described under [Scheduled sync](#scheduled-sync).

Run commands from the AIS-OS checkout with its existing requests dependency, or use `uv run --with requests python scripts/canvas.py ...`.

## Operator commands

```bash
python scripts/canvas.py probe
python scripts/canvas.py map
python scripts/canvas.py sync
python scripts/canvas.py status
python scripts/canvas.py courses
python scripts/canvas.py due --period week
python scripts/canvas.py due --period next-seven-days --unfinished
python scripts/canvas.py assignments --course STDISCM --limit 20 --offset 0
python scripts/canvas.py detail --course STDISCM --id 123
python scripts/canvas.py grades --course STDISCM
python scripts/canvas.py announcements --course STDISCM
python scripts/canvas.py deliver
```

The example assignment ID is illustrative. Use an ID returned by `assignments`.

`map` reads the active wiki term and all paginated Canvas courses. It requires a unique match for each subject's code, section and academic term. It saves private candidates for inspection when matching fails. It never guesses or returns a partial mapping. Current automatic term matching accepts forms such as `AY 2026-2027 Term 1`; an unrecognized format requires inspection before changing the matcher. Course mappings and the account ID stay outside Git. A changed wiki manifest requires mapping again.

`sync` checks that the authenticated account matches the mapping. It makes sequential GET requests and commits each complete course/category independently. A failed or malformed category retains its previous data and successful-fetch timestamp. Successful empty lists represent an empty category; failure never means deletion. Records absent from a complete snapshot become inactive, with prior values retained for transition comparison.

Queries and notification previews open SQLite with `mode=ro` and `query_only`. They never open credentials, acquire the writer lock, initialize a database, migrate a schema or create required sidecars. Missing databases return a JSON error and a nonzero exit. Use these commands in bound workers; run `map`, `sync` and actual delivery only through an operator or coordinator that owns writes. This PR grants no worker a refresh operation or additional filesystem access.

Queries return coverage and fetch timestamps for their relevant categories, plus authentication state. A category becomes stale after four hours. Restored authentication does not refresh old facts. `grades` returns assignment grades in paged `data` and every selected course grade in `course_grades`, with coverage for both. Course grades remain visible on every page. Null values remain unknown. Missing assignment grade fields do not block deadlines or submission state. Each assignment grade reports `grade_available` and `grade_success_at`; unavailable grades retain any earlier verified value and timestamp. Grade-query coverage reports missing or stale assignment grades separately from fresh assignment facts. Week boundaries use Monday 00:00 through next Monday 00:00 in Asia/Manila. The end is exclusive. Submitted work remains included unless `--unfinished` is requested.

Flags that do not apply to a command are rejected. `--unfinished` is for `due` and `assignments`; `--period` is for `due`; pagination is for list queries. List queries return 50 records by default, with `total` and `next_offset`; `--limit` accepts 1 through 200. Assignment descriptions appear in `detail`. Announcement lists shorten bodies to 1,000 characters and mark truncation. Pass `--id` to retrieve the stored body for one announcement. Source links use fixed Canvas paths constructed from IDs. HTML tags and embedded URLs are removed from stored descriptions, so signed content links are not passed to agents or Telegram. Full document retrieval belongs to the later materials milestone.

## Private files and locking

Credentials and control files live under `~/.config/achios/canvas/` with directory mode 700 and file mode 600. The client reads `cookies.txt` as a Mozilla cookie jar, saves response updates atomically and refuses redirects. Every initial request and pagination link must stay on the DLSU HTTPS API origin. Network failures, permission denial, expired authentication and malformed responses have separate error codes. Exceptions do not include response bodies, cookies or request URLs. Requests disable inherited proxy and netrc behavior.

`mappings.json` holds verified subject/course mappings. `course-candidates.json` holds private metadata for operator inspection. `receipt.json` holds the last completed online command result, including failures reached after the client opens. `probe` and successful `map` also record authentication in the selected database. An observed expiry updates cached warnings immediately, and recovery does not change category fetch timestamps. These are writer commands. Session-cookie expiry metadata is not evidence of server-session lifetime.

The database defaults to `~/.local/share/achios/canvas/canvas.sqlite3`. Its initial version is 1, with foreign keys and DELETE journaling. DELETE journaling lets readers use a protected directory without WAL shared-memory files. Reads hold a SQLite read transaction for consistent records and coverage. A reader that encounters a hot journal requiring recovery fails without writing; the coordinator must open the database to recover it.

One nonblocking `writer.lock` covers the client, mapping, sync and live delivery. Competing writers return `busy`. Future phone reauthentication must take the same lock before replacing the cookie jar. Use one canonical config directory for all writers. `--config`, `--db` and `--wiki` support isolated tests and operator paths; a future coordinator must validate its own arguments and must not forward arbitrary worker paths.

## Notification delivery

`deliver` previews up to 50 pending or uncertain events and reports the remaining count. It sends nothing. After reviewing the preview, an operator can send through the shared school sender:

```bash
python scripts/canvas.py deliver --send
```

This uses `scripts/telegram_notify.py` and requires both values in `~/.config/achios/telegram_school.env`, preventing fallback to a different inherited bot configuration.

Each course/category's first successful snapshot is silent. Later new assignments, changed due dates, new announcements and changed grades create events in the same transaction as their snapshot. Description-only edits remain silent. Authentication expiry and recovery each create one event per observed transition; an initial successful probe is silent.

An SQLite sequence gives each event its own durable ID. Repeated A to B to A to B changes retain both A to B events. Re-fetching the same snapshot does not create another event. Delivery marks an event uncertain before sending and records success only after the shared sender returns success. A crash after sending but before recording success can cause a duplicate on retry. A failed send preserves the event and lets later events in the batch proceed. Batches select the least-attempted events first, then event ID, so repeatedly rejected events cannot keep new alerts beyond the first 50 waiting forever. The result names failed event IDs and stays nonzero while the batch has failures. A positive shared-sender receipt confirms delivery even if the sender split the message into several parts. No model calls occur in these operations.

Synthetic preview from the regression fixtures, not a live class notification:

```text
STDISCM
Due date changed: Lab
Previous: Tue 08 Sep, 08:00 AM Manila
Now: Wed 09 Sep, 08:00 AM Manila
https://dlsu.instructure.com/courses/42/assignments/1
```

## Verification and remaining acceptance

```bash
uv run --with pytest --with requests python -m pytest tests/ -q
```

The full command returned 398 passed in 50.10s. The final enrollment-query adjustment then passed 27 targeted store, event and CLI tests.

The Canvas tests cover hostile URLs, pagination failures, cookie persistence, bounded retries, partial snapshots, time boundaries, null values, rollback, repeated events and uncertain delivery. The boundary test requires the achiCore sibling checkout and a Linux kernel with Landlock. It verifies an actual denied write before reading the database under that boundary, rather than relying on mocked permission checks.

A live Ubuntu probe on 2026-09-08 at 18:26 UTC returned `authentication_expired`. This is new evidence, not the successful September 7 experiment. At that checkpoint, course mapping and factual sampling were unverified. No live Telegram send, phone login or timer activation has passed in this work. The resumed session restored Ubuntu authentication at 22:34 UTC and matched all five subjects, which Aki confirmed. Aki also confirmed sampled CCINOV8 deadlines and clarified that the visible 0/0 was a What-If score, not a posted grade. STDISCM announcements and deadlines were visible through the API; missing grade fields exposed the validation issue corrected in this revision. Retest changed behavior at the new head and keep incomplete acceptance gates open. Notification unit tests and previews do not establish deployed delivery reliability.

After the session is restored privately, run `probe`, then `map`. Inspect all five mappings privately. Run `sync` and compare sampled effective dates, submission states, grades and announcements against Canvas. Inspect `status` and `deliver` before any live sending. Production deployment remains gated by the phone-login and hub-integration tickets.

## Scheduled sync

`systemd/achios-canvas-sync.timer` starts `achios-canvas-sync.service` at :00 and :30. The service is a oneshot that runs `scripts/canvas_scheduled.py`: one `sync` across every mapped course and category, then `deliver --send`. Delivery follows a failed or partial sync too, because sync queues the session-expired notice before exiting nonzero. A run that finds the writer lock held skips delivery, since a manual Refresh now or an earlier run owns the cache. Both steps use the shared `writer.lock`, so the timer and Telegram's Refresh now never write at once.

No model calls occur. Retries come from the client's three bounded attempts per request and from the next half-hour run; the unit has no `Restart=`. `TimeoutStartSec=10min` bounds a hung run, and killing the process releases the lock. `Persistent=true` makes systemd start one catch-up run after downtime, never one per missed slot. Events come only from the difference between the saved snapshot and the current fetch, so the catch-up run reports current changes rather than replaying obsolete ones. Expiry, network loss and failed courses keep saved facts. Four-hour staleness stays per course and category.

The service exits nonzero only for local faults such as a missing mapping, unreadable cache, cookie store or school notification config. Those fire the existing `achios-failure-alert@`. Expired sessions, Canvas errors, partial categories, unconfirmed delivery and a held lock exit 0. They reach Aki through the one-time Canvas notices and stale flags instead of an alert every 30 minutes. Each run appends one JSON line with sync and delivery results to `~/.local/state/achios/canvas_sync.log`; the unit's `UMask=0077` keeps new files private. The line carries counts, subject codes and error kinds, never grades, cookies or URLs.

Email notifications from `email_digest.py` are unchanged until direct sync has shown reliability.

### Reminders and digests

Between `sync` and `deliver --send` the service runs `canvas.py remind` ([#37](https://github.com/achibukz/AIS-OS/issues/37)). It takes `writer.lock`, reads the cache and queues notices as ordinary events, so they share delivery, retry and the uncertain state. It runs after a failed sync too, which keeps reminders coming from saved facts during an outage. Unfinished work uses the same rule as `--unfinished`. Times are Asia/Manila.

| Notice | When | Messages |
|---|---|---|
| Catch-up | First run that finds no `catchup:v1` key | Deadlines from now, latest announcement per course, course grades |
| Weekly | Monday at or after 08:00 | Deadlines Monday through Sunday, announcements from the past 7 days, course grades |
| Daily | Tuesday to Sunday at or after 08:00 | Deadlines before the next 08:00, plus announcements only when posted in the past 24 hours |
| 3h reminder | Due in at most 3 hours and more than 1 hour | One per assignment and due date |
| 1h reminder | Due in at most 1 hour | One per assignment and due date |

Empty weeks and days still send "nothing due". The run that sends the catch-up claims that day's digest without sending it. Schema version 2 adds `notices(key, created_at)`; each claimed key commits with its events. Keys are `catchup:v1`, `weekly:<ISO year-week>`, `daily:<date>` and `reminder:<course>:<assignment>:<due_at>:<3h|1h>`. A changed due date is a new key, so its reminders re-arm. Only current windows count, so downtime never replays a missed day or an elapsed reminder. Writers migrate version 1 caches; readers accept both.

Deadline messages are a countdown, soonest first, rendered when sent rather than when queued. Every assignment, announcement, grade or other Canvas item in any message is followed by its stored `source_url`. Auth notices name no item and carry no link.

```text
Due this week (2)
• in 16h  STDISCM  Lab 3 (Mon 11:59 PM)
  https://dlsu.instructure.com/courses/42/assignments/1
• in 2d   CCINOV8  Pitch deck draft (Wed 08:00 AM)
  https://dlsu.instructure.com/courses/43/assignments/7
Data as of Mon 14 Sep, 07:30 AM
```

Preview what the next run would queue against a copy of the cache, never the live file:

```bash
tmp=$(mktemp -d); cp ~/.local/share/achios/canvas/canvas.sqlite3 "$tmp/cache.sqlite3"
python scripts/canvas.py --config "$tmp/config" --db "$tmp/cache.sqlite3" remind
python scripts/canvas.py --config "$tmp/config" --db "$tmp/cache.sqlite3" deliver
```

Roll back by redeploying the previous `canvas_scheduled.py`. The `notices` table can stay; a version 2 cache still serves reads.

### Preview, deploy and rollback

Do not run `scripts/install_units.sh` for this. It re-enables every timer in `systemd/`, including ones deliberately left off.

```bash
repo=~/Code/GitHub/AIS-OS
dest=~/.config/systemd/user
# Preview: pending notices the next run would send, and rendered-unit checks
~/.local/share/achios/venv/bin/python "$repo/scripts/canvas.py" deliver
for unit in achios-canvas-sync.service achios-canvas-sync.timer; do
  sed "s|@REPO@|$repo|g" "$repo/systemd/$unit" > "/tmp/$unit"
done
systemd-analyze --user verify /tmp/achios-canvas-sync.service /tmp/achios-canvas-sync.timer
# Deploy
for unit in achios-canvas-sync.service achios-canvas-sync.timer; do
  sed "s|@REPO@|$repo|g" "$repo/systemd/$unit" > "$dest/$unit"
done
systemctl --user daemon-reload
systemctl --user enable --now achios-canvas-sync.timer
systemctl --user list-timers achios-canvas-sync.timer --no-pager
# One run on demand, then its result
systemctl --user start achios-canvas-sync.service
tail -n 1 ~/.local/state/achios/canvas_sync.log
# Rollback
systemctl --user disable --now achios-canvas-sync.timer
rm "$dest/achios-canvas-sync.service" "$dest/achios-canvas-sync.timer"
systemctl --user daemon-reload
```

Rollback leaves the cache, mappings, cookies and queued events in place. Telegram Refresh now keeps working without the timer.

## API references

The [Canvas assignment API](https://developerdocs.instructure.com/services/canvas/resources/assignments) defines `due_at` as effective for the requesting user and supports including that user's submission. The client also uses the [courses API](https://developerdocs.instructure.com/services/canvas/resources/courses), [enrollments API](https://developerdocs.instructure.com/services/canvas/resources/enrollments), and the [discussion topics API](https://developerdocs.instructure.com/services/canvas/resources/discussion_topics) with `only_announcements=true` to avoid the global announcements endpoint's default date window.

## Assisted feature live testing

Copy this invocation into an assistant session on achibuntu:

```text
Use the assisted-live-testing skill on https://github.com/achibukz/AIS-OS/pull/33.
Read the current PR, review comments and acceptance criteria for #26, #28 and #29.
Pin its current head and use an isolated checkout containing that exact commit.
Resume the private record at ~/.local/state/assisted-live-testing/canvas-pr33/record.md
if it exists, but distinguish old-head observations from tests of the current head.
Run on achibuntu using the existing private Canvas jar and schoolWiki read-only.
Use a run-owned SQLite database outside the checkout. Do not deploy, merge, change
Canvas data or send Telegram messages without first showing the exact preview.
I perform login/MFA and compare browser facts; you run the commands and inspect results.
Produce a redacted Markdown interaction/evidence record and post a concise comment
on PR #33 with the tested head, results, failures, open gates and the record link.
```

Prerequisites are the Ubuntu checkout at the pinned PR head, Python with requests, the achiCore sibling for boundary tests, the read-only schoolWiki manifest, and a valid private Canvas cookie jar. The Mac may provide the initial session through private SSH. That does not pass the separate phone-only login gate. Never put cookies, signed URLs or grades in public receipts.

The assistant chooses a private run directory and passes its database path explicitly to every command, including `probe`. No background service should use this test database. Preserve earlier evidence when starting a fresh database after a head change.

| Step | Assistant action | Human action | Expected result and receipt |
|---|---|---|---|
| Pin | Read PR head and compare `git rev-parse HEAD` | None | Exact SHA recorded before testing |
| Authenticate | Run `canvas.py --db <run-database> probe` | Log in and transfer privately only if needed | Exit 0 and redacted auth receipt; no secret output |
| Map | Run `canvas.py --db <run-database> map` | Confirm displayed subject/section/term matches | Five unique matches, private mappings and timestamp |
| Sync | Run `canvas.py --db <run-database> sync`, then `status` | None | Complete categories or explicit partial coverage; no silent loss |
| Compare | Run `due`, `assignments`, `grades` and `announcements` against the run database | Compare one supplied example at a time with Canvas, excluding What-If scores | Per-case match or mismatch, fetch time and user report recorded privately |
| Repeat | Sync again, then run `deliver` without `--send` | Review preview if any | Silent initial baselines and no duplicate events for unchanged facts |
| Deliver | After explicit approval, send the reviewed event through the existing school sender | Confirm arrival in achiSchooNounce | Live outbound receipt and user confirmation, or not run |

A successful partial fetch does not establish coverage of an unavailable grade. Report automated tests, live API responses and human comparisons separately. Do not call phone login, manual hub refresh or timer activation passed from this PR's CLI tests. Those remain #27, achiCore #173 and #30.
