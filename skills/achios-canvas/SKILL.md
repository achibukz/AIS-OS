---
name: achios-canvas
description: Read Aki's cached Canvas courses, assignments, due dates, grades, and announcements from any repository, including schoolMem.
---

# Canvas reads

Use Python 3.11 or newer and the bundled `scripts/access.py`, resolved relative to
this skill's directory. Reads go through achiOS's existing cache reader.

```bash
python3 <skill-dir>/scripts/access.py canvas status
python3 <skill-dir>/scripts/access.py canvas courses
python3 <skill-dir>/scripts/access.py canvas due --period next-seven-days --unfinished
python3 <skill-dir>/scripts/access.py canvas assignments --course STDISCM
python3 <skill-dir>/scripts/access.py canvas detail --course STDISCM --id ASSIGNMENT_ID
python3 <skill-dir>/scripts/access.py canvas grades --course STDISCM
python3 <skill-dir>/scripts/access.py canvas announcements --course STDISCM
```

Read `status` to establish cache freshness. Use the course keys returned by
`courses`. Handle pagination for full results. State the fetch timestamp when
answering questions that depend on current data.

The cache defaults to the operator's `.local/state/achios/canvas/canvas.sqlite3`.
`ACHICORE_CANVAS_DB` selects an existing cache explicitly. Pulling achiOS installs
code and instructions; it does not create a Canvas cache on the Mac.

If the cache is missing, say so and offer a read on the configured achibuntu host
through an existing SSH connection. Do not invent an SSH alias, sync an open SQLite
database, or report an empty schedule. Google OAuth does not authenticate Canvas.

Refresh, event delivery and phone login belong to the coordinator. Use the existing
hub's Refresh now and Start phone login controls. A CLI session may request a
coordinator refresh through an available authorized control, but installing this
skill does not provide a new one. Never run `probe`, `map`, `sync`, or notification
delivery from a bound read turn, and never print cookies or private config files.
