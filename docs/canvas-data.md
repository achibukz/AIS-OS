# Canvas client, cache and notifications

This implements the source work for [#26](https://github.com/achibukz/AIS-OS/issues/26), [#28](https://github.com/achibukz/AIS-OS/issues/28) and [#29](https://github.com/achibukz/AIS-OS/issues/29). It does not install a service or connect schoolMem. Phone login remains [#27](https://github.com/achibukz/AIS-OS/issues/27), hub integration remains [achiCore #173](https://github.com/achibukz/achiCore/issues/173), and scheduling remains [#30](https://github.com/achibukz/AIS-OS/issues/30).

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

Queries return coverage and fetch timestamps for their relevant categories, plus authentication state. A category becomes stale after four hours. Restored authentication does not refresh old facts. `grades` includes assignment grades and course grades, with coverage for both. Null values remain unknown. Week boundaries use Monday 00:00 through next Monday 00:00 in Asia/Manila. The end is exclusive. Submitted work remains included unless `--unfinished` is requested.

List queries return 50 records by default, with `total` and `next_offset`; `--limit` accepts 1 through 200. Assignment descriptions appear in `detail`. Announcement lists shorten bodies to 1,000 characters and mark truncation. Pass `--id` to retrieve the stored body for one announcement. Source links use fixed Canvas paths constructed from IDs. HTML tags and embedded URLs are removed from stored descriptions, so signed content links are not passed to agents or Telegram. Full document retrieval belongs to the later materials milestone.

## Private files and locking

Credentials and control files live under `~/.config/achios/canvas/` with directory mode 700 and file mode 600. The client reads `cookies.txt` as a Mozilla cookie jar, saves response updates atomically and refuses redirects. Every initial request and pagination link must stay on the DLSU HTTPS API origin. Network failures, permission denial, expired authentication and malformed responses have separate error codes. Exceptions do not include response bodies, cookies or request URLs. Requests disable inherited proxy and netrc behavior.

`mappings.json` holds verified subject/course mappings. `course-candidates.json` holds private metadata for operator inspection. `receipt.json` holds the last completed online command result, including failures reached after the client opens. Session-cookie expiry metadata is not evidence of server-session lifetime.

The database defaults to `~/.local/share/achios/canvas/canvas.sqlite3`. Its initial version is 1, with foreign keys and DELETE journaling. DELETE journaling lets readers use a protected directory without WAL shared-memory files. Reads hold a SQLite read transaction for consistent records and coverage. A reader that encounters a hot journal requiring recovery fails without writing; the coordinator must open the database to recover it.

One nonblocking `writer.lock` covers the client, mapping, sync and live delivery. Competing writers return `busy`. Future phone reauthentication must take the same lock before replacing the cookie jar. Use one canonical config directory for all writers. `--config`, `--db` and `--wiki` support isolated tests and operator paths; a future coordinator must validate its own arguments and must not forward arbitrary worker paths.

## Notification delivery

`deliver` previews up to 50 pending or uncertain events and reports the remaining count. It sends nothing. After reviewing the preview, an operator can send through the shared school sender:

```bash
python scripts/canvas.py deliver --send
```

This uses `scripts/telegram_notify.py` and requires both values in `~/.config/achios/telegram_school.env`, preventing fallback to a different inherited bot configuration.

Each course/category's first successful snapshot is silent. Later new assignments, changed due dates, new announcements and changed grades create events in the same transaction as their snapshot. Description-only edits remain silent. Authentication expiry and recovery each create one event per observed transition; an initial successful probe is silent.

An SQLite sequence gives each event its own durable ID. Repeated A to B to A to B changes retain both A to B events. Re-fetching the same snapshot does not create another event. Delivery marks an event uncertain before sending and records success only after the shared sender returns success. A crash after sending but before recording success can cause a duplicate on retry. A failed send stops the current batch and preserves the event for a later invocation. No model calls occur in these operations.

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

A live Ubuntu probe on 2026-09-08 at 18:26 UTC returned `authentication_expired`. This is new evidence, not the successful September 7 experiment. No current course-ID mapping, current factual sampling, live Telegram send, phone login or timer activation has passed in this work. Keep #26 and #28 open until their live acceptance passes. Notification unit tests and previews do not establish deployed delivery reliability.

After the session is restored privately, run `probe`, then `map`. Inspect all five mappings privately. Run `sync` and compare sampled effective dates, submission states, grades and announcements against Canvas. Inspect `status` and `deliver` before any live sending. Production deployment remains gated by the phone-login and hub-integration tickets.

## API references

The [Canvas assignment API](https://developerdocs.instructure.com/services/canvas/resources/assignments) defines `due_at` as effective for the requesting user and supports including that user's submission. The client also uses the [courses API](https://developerdocs.instructure.com/services/canvas/resources/courses), [enrollments API](https://developerdocs.instructure.com/services/canvas/resources/enrollments), and the [discussion topics API](https://developerdocs.instructure.com/services/canvas/resources/discussion_topics) with `only_announcements=true` to avoid the global announcements endpoint's default date window.
