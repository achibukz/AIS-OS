---
name: achios-planning
description: Read Aki's shared tasks and Google Calendar from any repository, or reconcile an authorized task or deadline change through achiOS's existing writer.
---

# Shared tasks and Calendar

Use Python 3.11 or newer and the bundled `scripts/access.py`, relative to this skill's
resolved directory. The task register belongs to achiOS even when the current repo
is schoolMem or a coding project. It is a local checkout snapshot, not a live view of
another machine's unpushed changes.

```bash
python3 <skill-dir>/scripts/access.py tasks all
python3 <skill-dir>/scripts/access.py tasks school
python3 <skill-dir>/scripts/access.py calendar calendars list
python3 <skill-dir>/scripts/access.py calendar agenda --from 2026-10-01 --to 2026-10-07
python3 <skill-dir>/scripts/access.py calendar events list --calendar DLSU --from 2026-10-01 --to 2026-10-07
```

Use Asia/Manila when resolving "today" and deadlines. Replace sample dates with
the requested window. The Calendar reader uses the private calendar configuration
and existing Google profiles. Do not invent calendar IDs or copy credentials into
this repo. If configuration is missing on the Mac, report it; do not recreate the
server's calendar policy from memory.

For an authorized mutation, locate achiOS by resolving the bundled script and
read the affected task and current calendar configuration first. Use its existing
`scripts/cohesion.py submit --input request.json` for linked task and Calendar
changes. Inspect `submit --help` and the request contract in `scripts/cohesion.py`
before preparing the request. That writer records stable IDs and partial outcomes.
Do not rewrite linked tasks directly or mark a partial operation complete.

Existing placement preferences apply: social plans use Calendar, quick tasks and
coding tickets use tasks, and school deadlines use linked records in both. A date
alone does not create an appointment. Honor an explicit placement for this item.

Calendar writes still belong to Asa, Asta, or cohesion under the configured owner.
Do not impersonate a writer merely because the CLI accepts an owner string. A
single explicitly requested event needs no repeated confirmation. Several events,
a move, or a deletion require the existing Calendar confirmation. Pass the read
etag when updating so newer edits are preserved. An unavailable or disallowed
writer remains a pending action.

Report what the command actually changed, including its receipt and any remaining
work. Reading this skill does not grant write access to another repo or vault.
