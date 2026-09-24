# Scoped semantic preferences

AIS-OS #14 adds sourced, versioned preferences to the cohesion database. The
Telegram handler owns source identity and validates every proposed evidence quote
against the captured user message. Assistant text, legacy TGDB output and an
unvalidated quote cannot activate a rule.

The first supported preference kinds are file delivery, task and Calendar
placement, and linked completion. Scope can be global, category or item. Item
scope wins over category, and category wins over global. A current explicit
instruction still wins over every learned value. "This one" therefore changes
one item, while an explicit category phrase can affect later matching items.

Each proposal stores its source, exact evidence, scope, exceptions, state and
revision. Corrections append an event and increment the active preference revision.
Revocation keeps the event history and removes the value from active context.
Ambiguous scope stays pending and returns one concise question. The current item
repair can still complete before that question is answered.

`scripts/learning_ledger.py` mirrors each event and transition in append-only JSONL.
`scripts/cohesion.py context` returns active semantic preferences and up to 20
inspectable pending or rejected events. Retrieval and application remain separate.

## Daily review

`achios-semantic-review.timer` runs at 03:00 Asia/Manila and catches a missed run
after downtime. `scripts/semantic_review.py` reads pending rows, including rows
behind its durable checkpoint. An idle run makes no model call.

The reviewer calls `gemini-3.8-flash` at high effort through the native agy CLI, with no
API key. It runs headless in an empty directory, where agy auto-denies any tool that needs
permission, and an answer that lists a denied action is discarded. Our prompt is capped at
6,000 bytes, the answer at 1,000 tokens excluding thinking, and the call at 300 seconds.
One retry is allowed. Every
attempt reserves one of 24 calls for the current Manila day inside an immediate
SQLite transaction. A file lock permits one classifier at a time. A missing
agy, provider failure, invalid output or an exhausted budget leaves the evidence
pending. No fallback model runs.

Install the checked-in unit and timer through `scripts/install_units.sh`. It needs no
key, only a signed-in `~/.local/bin/agy`.
The script prints one structured summary suitable for achiNouncements delivery.

## Rollback

Disable `achios-semantic-review.timer` first. Deploying older code leaves the new
SQLite tables untouched. Older cohesion code ignores them and continues using its
seeded placement table. Restore the pre-deployment cohesion database backup only
if the semantic event history must also be removed.
