# Connections

Registry of every system achiOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | Phone money manager app (name TBD) + allowance | not yet connected | — | — |
| 2 | Customer interactions | Gmail (akibukzwork@gmail.com — recruiters/career) | not yet connected | — | — |
| 3 | Calendar | Google Calendar (both Gmails) | not yet connected | — | — |
| 4 | Communication | Discord (thesis) + Messenger (school/personal groups) + DLSU Gmail (abram_bukuhan@dlsu.edu.ph) | not yet connected | — | — |
| 5 | Project / task tracking | Canvas LMS (school tasks) + achiMem (general — proposed) + achiOS (this repo, project specs) | partial — Canvas reachable via `/canvas-tracker` (Chrome session, see `~/.claude/CLAUDE.md` memory) | session cookie via Claude in Chrome | 2026-06-13 |
| 6 | Meeting intelligence | Thesis F2F notes → schoolMem/raw → schoolMem/wiki; class material likewise | partial — manual ingestion today; `ingest-batch` skill exists | — | — |
| 7 | Knowledge / files | Obsidian: schoolMem (~/Documents/Obsidian/schoolMem, primary) + achiMem (~/Documents/Obsidian/achiMem). CV/cover-letter docs: `career-ops` repo. | local files — no API yet | — | 2026-06-15 |

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `not yet connected`.

When you wire a new tool, also save `references/{tool}-api.md` capturing endpoints, auth flow, and common queries — researched-once-saved-forever.

## Related repos (not connections, but reachable locally)

- `~/Code/GitHub/career-ops` — application pipeline, CV/cover letter generation, follow-up cadence. `data/applications.md` is the source of truth for active applications.
- `~/Code/GitHub/sfv-thesis` — thesis source, chapters, dataset pipeline.
- `~/Documents/Obsidian/schoolMem` — Obsidian vault (school notes + thesis meeting minutes).
- `~/Documents/Obsidian/achiMem` — Obsidian vault (general / non-school).
