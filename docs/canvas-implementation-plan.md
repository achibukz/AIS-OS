# Canvas integration implementation plan

Approved by Aki on 2026-09-08 after the design interview. Parent: [AIS-OS #24](https://github.com/achibukz/AIS-OS/issues/24).

This approved plan and the linked tickets supersede the research draft preserved below. The research's course examples, 30-minute interval, phase ordering, optional phone login and exactly-once notification claims are not implementation requirements.

## First release

schoolMem answers deadlines, submission status, personal grades and announcements using compact queries against a local SQLite database. achiSchooNounce receives deterministic change notifications through the existing shared sender. The active topic engine handles user questions; no code assumes Claude specifically.

Scheduled sync, event detection and message formatting make zero model calls. Document ingestion, file downloads, FTS search and vault copying follow after the first release. Discussions remain optional.

## Course selection

Read the explicitly active term from schoolMem/wiki/index.md, then its Subjects table. Do not choose a term from the date, directory order or all courses still enrolled on Canvas. Current observed selection is AY2627-T1:

| Subject | Section |
|---|---|
| CCINOV8 | S03 |
| GELITPH | Y11 |
| STDISCM | S03 |
| STSP002 | S30A |
| THS-ST2 | S03 |

Read schoolWiki without modifying it. Match these subjects against authenticated Canvas course metadata by course, section and term. Save verified course-ID mappings privately. Missing or ambiguous matches require inspection and, if evidence cannot resolve them, Aki's choice. Course IDs have not yet been verified.

## Schedule and query rules

- Refresh every 30 minutes, with a manual Refresh now action. #30 shortened the approved two-hour interval.
- Use Asia/Manila. This week means Monday 00:00 through next Monday 00:00, with an exclusive end. Next seven days is a separate request.
- Include submitted assignments with their status unless unfinished work is explicitly requested.
- Include relevant successful-fetch timestamps in factual answers. Flag data older than four hours, or authentication failure immediately when detected.
- Track freshness, coverage and initial baselines per course and data category. A successful assignments fetch does not claim fresh grades or announcements.
- Preserve and answer from saved data after failure. Successful authentication alone does not refresh old data.

## Phone reauthentication is required

Aki accepts opening a link from Telegram in Safari or Chrome with Tailscale connected. The link must reach a protected browser running on Ubuntu. Aki performs Google login and MFA himself. The resulting Canvas session remains private on Ubuntu.

Inspect existing remote-browser access first. Prove the flow with the Mac closed and an authenticated Ubuntu API request after login. A plain Canvas link on the phone or a Mac cookie export does not pass this gate. If Google rejects the proposed browser, keep the gate open and revise the approach. Do not present a candidate mechanism as working.

Session lifetime remains measured evidence, not an assumed cookie duration. The client preserves response cookie changes, but periodic reads are not claimed to defeat expiry.

## Storage and execution ownership

AIS-OS owns the client, SQLite store, scheduled writer, events and private cache. achiCore owns schoolMem routing and the explicit refresh request path.

Bound agents cannot write ~/.local/share under the current achiCore boundary. Cached queries must open the database read-only without initialization, migration or required sidecar creation. Manual refresh must use an explicit coordinator-owned operation with authorization, argument validation and concurrency control. Do not weaken the write boundary to make a worker's CLI write the cache.

Store credentials under ~/.config/achios/canvas with owner-only permissions. Never put credentials, authenticated URLs or session values in Git, logs, Telegram or the vault. Test origin restrictions on pagination and redirects as well as initial requests.

## Events and delivery

Notify new assignments, due-date changes, new announcements, grades posted or changed, and authentication expired or restored. Description-only edits remain queryable and silent. Initial successful imports are silent per course/category.

Commit snapshot updates and detected events together. Assign each observed transition an identity that survives replay and preserves repeated changes such as A to B to A to B. A hash of only the old and new values is insufficient.

Persist pending deliveries and record successful sending afterward. A crash or network ambiguity can leave delivery uncertain. Aki accepts retrying with a rare duplicate rather than losing an alert; do not promise exactly-once messages. Auth notices occur once per outage/recovery. Keep email notifications unchanged until direct Canvas coverage and reliability justify deduplication.

## Incremental tickets

| Ticket | Scope |
|---|---|
| [achibukz/AIS-OS#25](https://github.com/achibukz/AIS-OS/issues/25) | read the active-term subject manifest from schoolWiki |
| [achibukz/AIS-OS#26](https://github.com/achibukz/AIS-OS/issues/26) | build the cookie HTTP client and verify current-term course mappings |
| [achibukz/AIS-OS#27](https://github.com/achibukz/AIS-OS/issues/27) | prove phone reauthentication through a protected Ubuntu browser |
| [achibukz/AIS-OS#28](https://github.com/achibukz/AIS-OS/issues/28) | sync factual data into SQLite and expose compact queries |
| [achibukz/AIS-OS#29](https://github.com/achibukz/AIS-OS/issues/29) | persist change events and deliver achiSchooNounce notifications |
| [achibukz/achiCore#173](https://github.com/achibukz/achiCore/issues/173) | connect schoolMem factual queries and Refresh now |
| [achibukz/AIS-OS#30](https://github.com/achibukz/AIS-OS/issues/30) | schedule 30-minute sync and verify the first Telegram release |
| [achibukz/AIS-OS#31](https://github.com/achibukz/AIS-OS/issues/31) | follow-up course materials, file cache and FTS search |

Start with #25, then #26. After #26, phone login #27 and factual storage/queries #28 can proceed independently. #29 follows #28. achiCore #173 follows #27 and #28. AIS-OS #30 waits for all first-release pieces; #31 is a later milestone.

Every ticket names its dependencies, acceptance checks and an existing recommended executor model. The parent epic is context, not a circular blocker. Work stays in this Codex task unless Aki explicitly changes his single-session execution rule.

## Verification and release

Use fixtures for malformed wiki inputs, authentication/permission failures, pagination, cookie persistence, time boundaries, partial state, transaction replay, notification ambiguity and unauthorized refresh. Tests must exercise the real read-only database behavior under the worker boundary.

Live acceptance separately checks current-term course mappings, sampled dates/submissions/grades/announcements, phone login with the Mac closed, manual refresh, timer activation and Telegram delivery. Prepare previews and redacted receipts before assisted phone steps. No service is deployed merely by adding its source.

## Status at approval

The 2026-09-07 experiment verified Ubuntu access with the Mac closed and a PDF download. It did not measure overnight session lifetime. No production Canvas integration or recurring sync is deployed. Current wiki subjects have been read; Canvas IDs and phone login are pending. The offline subject manifest in #25 is implemented locally with 24 passing targeted tests and a successful read of the real current-term wiki. Review and merge remain pending.

## Historical research draft

The following is the original research, retained for background and API investigation. Its proposed tickets A through S are not the current work queue. Use the approved scope and GitHub tickets above when they differ.

---

Yes. After going deeper into the Canvas API, the current open-source Canvas-agent ecosystem, and your actual AIS-OS code, I would move from “experiment” to a **small production integration** now—but with authentication lifetime kept as an explicit unknown until the measurement finishes.

The main change I would make from my previous recommendation is this:

> **Use SQLite + files as the canonical local knowledge store, rather than a collection of JSON files.**
>
> Still no PostgreSQL, Redis, vector DB, dashboard, or additional service. SQLite is built for exactly the things this integration now needs: idempotent upserts, transactional partial-sync handling, deterministic deadline/grade queries, event diffing, and later FTS5 full-text search.

Your existing issue #24 remains a good parent/epic. Its current live checkpoint already establishes cookie-authenticated Ubuntu access, announcements/assignments/enrollment access, a discussion sample, and a verified authenticated PDF download; the unresolved items are mainly session lifetime, file-discovery completeness, course mappings, and production integration.

# 1. Target architecture

I would build this:

```
                         DLSU Canvas
                             │
                browser-derived Canvas session
                             │
                    ┌────────▼────────┐
                    │ canvas_client.py │
                    │ GET-only HTTP   │
                    │ cookie jar      │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
     canvas_sync.py                    canvas_download.py
            │                                 │
            ▼                                 ▼
    ┌─────────────────┐              ┌──────────────────┐
    │   canvas.db     │              │ Canvas file cache│
    │ SQLite + FTS5   │              │ PDF/PPTX/DOCX    │
    └────────┬────────┘              └────────┬─────────┘
             │                                │
             └──────────────┬─────────────────┘
                            │
                   achios-canvas CLI
                            │
             ┌──────────────┴──────────────┐
             │                             │
      canvas_events.py               schoolMem Claude
             │                       existing bot/session
             ▼                             │
     achiSchooNounce                       │
       deterministic                       ▼
       notifications                natural-language Q&A
                                      only retrieved context
```

This matches patterns used independently by several active projects. `canvasmcp` explicitly recommends its CLI as the primary stable interface and keeps MCP optional; `canvas-cli` emphasizes predictable JSON contracts and automatic pagination; `schoolbridge` separates deterministic LMS commands/event detection from the agent; and Canvas Course Downloader uses manifests, incremental fetching, module traversal, and embedded-file discovery.

## What I would _not_ add

For v1:

```
NO PostgreSQL
NO Redis
NO Chroma/Qdrant/Pinecone
NO FastAPI server
NO always-running Playwright
NO second Telegram framework
NO Canvas MCP server
NO autonomous Google/MFA agent
NO LLM inside the sync process
NO LLM-generated event detection
```

MCP can be added later as a thin wrapper around `achios-canvas` if another agent genuinely needs it.

---

# 2. Why SQLite is now the better local knowledge base

JSON was sufficient to prove the experiment. For the actual integration, SQLite gives you much cleaner answers to:

```
What is due this week?
Which things are unsubmitted?
What changed since yesterday?
Which grade changed?
Which announcement have I already notified Aki about?
Which file belongs to this course?
Search every STINTSY lecture for "cross validation".
```

without loading large files into Claude.

SQLite FTS5 is built into SQLite installations that include the extension and supports full-text indexing, BM25 ranking, snippets, phrase/prefix queries, and external-content tables. This is enough for a semester-sized educational knowledge base before embeddings are justified.

### Recommended private layout

```
~/.config/achios/canvas/
├── session.json
├── cookies.txt
└── config.json

~/.local/share/achios/canvas/
├── canvas.db
├── cache/
│   ├── 438921/
│   │   ├── 76532/
│   │   │   └── Lecture 04.pdf
│   │   └── ...
│   └── ...
├── extracted/
│   ├── 76532.txt
│   └── ...
├── receipts/
└── logs/
```

Permissions:

```
~/.config/achios/canvas/        0700
session/cookie files            0600
database/data                   user-readable only
```

No session credentials enter the repository or Obsidian vault.

---

# 3. Proposed data model

I would use a schema roughly like this.

### `courses`

```
canvas_id PK
name
course_code
term_name
workflow_state
start_at
end_at
enrollment_type
enrollment_state
enabled
last_seen_at
```

### `course_mappings`

I'd actually keep the authoritative mapping in private `config.json`, because absolute vault paths are machine-specific:

```
{
  "timezone": "Asia/Manila",
  "courses": {
    "438921": {
      "enabled": true,
      "alias": "STINTSY",
      "subject_key": "stintsy",
      "schoolmem_raw": "/actual/verified/path/STINTSY/raw"
    }
  }
}
```

Never infer the destination from `course.name`.

---

### `assignments`

```
canvas_id PK
course_id FK
name
description_html
description_text
html_url

due_at
unlock_at
lock_at

points_possible
grading_type
submission_types_json
published
updated_at

last_seen_at
```

One useful Canvas behavior here is that the assignment's `due_at` is calculated relative to the requesting user when assignment overrides exist. `include[]=all_dates` can still be retained for auditing/visibility into overrides, but for Aki's student account the normal effective assignment dates are particularly valuable.

I would therefore store both:

```
effective_due_at
all_dates_json
```

and compare sampled results against the Canvas UI before relying on it.

---

### `submissions`

```
assignment_id PK/FK
workflow_state
attempt
submitted_at
graded_at
posted_at

score
grade

late
missing
excused
late_policy_status

updated_at
```

Canvas exposes `workflow_state` values such as submitted/unsubmitted/graded/pending_review, plus late/missing information.

This means:

> “Have I submitted everything due tomorrow?”

is SQL, not AI.

---

### `enrollments`

```
course_id
enrollment_id
current_grade
current_score
final_grade
final_score
updated_at
```

Canvas enrollment grades can expose those four fields when the student is permitted to view them.

---

### `announcements`

```
canvas_id PK
course_id
title
message_html
message_text
posted_at
delayed_post_at
author_name
html_url
last_seen_at
```

The announcement endpoint accepts multiple `context_codes[]=course_ID` values and includes `context_code` in results, so announcements could efficiently be fetched across all enabled courses in one logical operation.

---

### `modules`

```
canvas_id PK
course_id
name
position
unlock_at
require_sequential_progress
state
```

### `module_items`

```
canvas_id PK
module_id
course_id

type
content_id
title
position

html_url
api_url

published
locked
```

Do **not** assume `include[]=items` always returns all items. Canvas explicitly says items may be omitted when a module has too many and clients must then call the module-items endpoint separately.

That deserves an automated test.

---

### `pages`

```
course_id
page_id
url_slug
title
body_html
body_text
created_at
updated_at
published
```

Canvas Pages expose the HTML body and modification timestamp, making them straightforward incremental knowledge-base documents.

---

### `files`

```
canvas_id PK
course_id

display_name
filename
content_type
size

canvas_url
updated_at

discovered_via
source_entity_type
source_entity_id

cache_state
local_path
sha256
extracted_path
extraction_state
```

`discovered_via` is useful:

```
files_api
module
page_link
assignment_link
announcement_link
discussion_link
```

because your live test has already shown that `/courses/:id/files` may be forbidden while content remains accessible elsewhere.

---

### `documents`

This is your searchable academic corpus:

```
id PK
course_id

source_type
source_id

title
body_text
source_url
updated_at
content_hash
```

Sources can include:

```
canvas_page
assignment
announcement
pdf
pptx
docx
discussion
```

---

### `documents_fts`

FTS5 over:

```
title
body_text
course_alias
```

Use:

```
bm25(documents_fts)
snippet(...)
```

for compact retrieval.

---

### `sync_runs`

```
id
started_at
finished_at
status

auth_state
courses_attempted
courses_successful
courses_partial

request_count
rate_limit_remaining_min

error_summary
```

Possible status values:

```
success
partial
auth_expired
failed
```

---

### `events`

```
id
event_key UNIQUE

event_type
course_id
entity_type
entity_id

before_json
after_json
summary

detected_at
notified_at
```

---

# 4. Authentication client design

This is important enough to be its own component.

The open-source `canvas-student-mcp` implementation confirms several cookie-auth quirks worth copying: manual redirect handling, XSSI-prefix stripping, login-page/non-JSON detection, and credential stripping before external file redirects. Its implementation treats a redirect as likely session expiry, handles `while(1);` before JSON parsing, and only supplies Canvas credentials while the current download URL remains on the Canvas host.

## `canvas_client.py`

Proposed interface:

```
class CanvasClient:
    def get_json(...)
    def get_paginated(...)
    def download(...)
    def probe_auth(...)
```

### It should enforce a fixed Canvas origin

```
CANVAS_ORIGIN = "https://dlsu.instructure.com"
```

Every ordinary API request must resolve to that origin.

Never allow callers to pass arbitrary:

```
https://whatever.com/
```

and still receive the cookie jar.

---

## JSON handling

Possible Canvas API response:

```
while(1);[{"id": ...}]
```

So:

```
if body.startswith("while(1);"):
    body = body[len("while(1);"):]
```

before decoding JSON.

The same issue is documented and implemented by `canvas-student-mcp`.

---

# 5. Authentication-state detection needs to be smarter than status codes

This is crucial.

You have already proven:

```
403 Files endpoint
```

does **not** necessarily mean:

```
expired session
```

Therefore this would be wrong:

```
if status in (401, 403):
    auth_expired()
```

Use typed errors:

```
CanvasAuthExpired
CanvasPermissionDenied
CanvasNotFound
CanvasRateLimited
CanvasTransientError
CanvasInvalidResponse
CanvasDownloadError
```

Possible `AUTH_EXPIRED` evidence:

```
302/303 redirect to /login
302 → /login/google
redirect to accounts.google.com
200 text/html where JSON expected + login markers
401 from otherwise known-authenticated endpoint
known profile/course probe no longer returns valid API JSON
```

Possible `PERMISSION_DENIED`:

```
403 JSON/API error
while another known-safe authenticated endpoint is still 200
```

That second check is useful:

```
/course/files → 403
       │
       ▼
/users/self/profile or /courses?per_page=1
       │
       ├── 200 JSON → permission failure
       └── login → auth failure
```

---

# 6. Session lifetime: don't design around 24 hours yet

Instructure's cookie policy currently describes `canvas_session` as the Canvas authenticated session ID and lists a 24-hour duration. However, your actual DLSU/Google-SSO behavior must still be measured; institution configuration and the behavior of refreshed/reissued cookies can affect what your Ubuntu client observes.

So the lifetime experiment should measure:

```
T+0
T+1 hour
T+6-ish / overnight
T+24h
T+48h if still alive
then daily until failure if useful
```

Record only:

```
{
  "checked_at": "...",
  "status": 200,
  "valid_json": true,
  "set_cookie_seen": true,
  "cookie_names_changed": ["..."]
}
```

Never cookie values.

---

# 7. Pagination

Every paginated endpoint should use:

```
Link: <...>; rel="next"
```

and follow the returned URL exactly.

Canvas specifically says these links should be treated as opaque and clients should not construct pagination URLs themselves.

So:

```
while next_url:
    response = request(next_url)
    rows.extend(response.json())
    next_url = parse_link_header(response.headers).get("next")
```

not:

```
page += 1
```

---

# 8. Rate limiting

For a single user's private sync, avoid concurrency complexity.

Canvas uses request-cost based throttling and returns `X-Request-Cost` and, when applicable, `X-Rate-Limit-Remaining`. Instructure notes that clients making no more than one simultaneous request are unlikely to be throttled, while parallel requests carry a preflight cost.

I'd start with:

```
max concurrency = 1
```

Possibly:

```
100–250 ms between content-heavy requests
```

when crawling lots of files/pages.

On `429`:

```
bounded exponential retry
respect Retry-After if provided
maximum 3–4 attempts
```

Do not infinitely retry.

---

# 9. Core sync algorithm

One production sync could look like this:

```
START sync run
    │
    ├── auth probe
    │      └── failed → stale/auth state + stop
    │
    ├── list all courses
    │
    ├── filter to configured enabled courses
    │
    ├── fetch announcements across enabled courses
    │
    └── for each course sequentially:
           │
           ├── assignments
           │      include[]=submission
           │      include[]=all_dates
           │
           ├── enrollment/self grades
           ├── modules
           │      include[]=items
           │      include[]=content_details
           │
           ├── module items if omitted
           ├── pages metadata
           ├── changed/new page bodies
           ├── files listing
           │       └── if 403 → mark listing forbidden, DON'T mark empty
           ├── discover File module items
           ├── discover /files/{id} HTML links
           └── optional discussions
    │
    ├── commit course snapshots independently
    ├── generate events from before/after
    ├── update FTS/extraction queue
    └── finish sync run
```

The course transaction boundary matters.

If:

```
STINTSY succeeds
CSOPESY succeeds
THSST1 fails
```

you want:

```
STINTSY = fresh
CSOPESY = fresh
THSST1 = previous data + stale/partial flag
```

rather than rolling the entire system back.

---

# 10. File discovery should be a graph

Do not think:

```
Canvas Files page = all files
```

Think:

```
                 Files API
                     │
                     ▼
                 file IDs
                     ▲
                     │
       ┌─────────────┼─────────────┐
       │             │             │
    Modules         Pages       Assignments
       │             │             │
       └─────────────┼─────────────┘
                     │
                Announcements
                     │
                 Discussions
```

The maintained Canvas Course Downloader explicitly searches assignments, pages, announcements, discussions and modules for linked files not visible in the ordinary file browser.

Another newer implementation, `learning-agent-canvas-extension`, uses a fallback chain of direct API → folders → module items → content-link discovery specifically because institution permissions can cause Files/Pages APIs to return 403.

A separate zero-dependency Canvas downloader independently documents the `/courses/:id/files` 403 workaround of finding File module items and resolving their `content_id`.

So I'd implement this sequence:

```
A. /courses/:course/files
B. modules → File module item → /files/:content_id
C. parse page HTML for Canvas file links
D. parse assignment descriptions
E. parse announcements
F. syllabus
G. discussions if enabled
```

Deduplicate by `canvas_file_id`, not filename.

---

# 11. File download security

The current successful live experiment got this right and production should preserve it.

Algorithm:

```
Canvas file metadata
       │
       ▼
Canvas-issued URL
       │
       ▼
request with redirect disabled
       │
       ├── redirect remains dlsu.instructure.com
       │       Canvas cookie permitted
       │
       └── redirect to CDN / S3 / external host
               NO Canvas cookies
       │
       ▼
download to:
filename.part
       │
       ▼
validate
       │
       ├── nonzero
       ├── expected size where known
       ├── content-type plausible
       └── magic bytes
       │
       ▼
SHA-256
       │
       ▼
atomic rename
```

`canvas-student-mcp` implements the same crucial credential boundary: credentials only ride along for same-host redirects; external download targets receive no authentication headers.

---

# 12. File validation

For PDFs:

```
body begins %PDF-
size > 0
metadata size matches when supplied
body is not Canvas login HTML
```

For ZIP-derived Office formats:

```
PPTX/DOCX/XLSX begin as ZIP/PK container
extension and content type plausible
```

And always:

```
SHA256(local bytes)
```

Store:

```
sha256
size
downloaded_at
canvas_updated_at
```

---

# 13. Extraction should also use 0 LLM tokens

### PDF

PyMuPDF supports normal PDF text extraction page-by-page.

```
PDF → PyMuPDF → per-page text
```

Store page boundaries:

```
=== PAGE 1 ===
...
=== PAGE 2 ===
...
```

Then schoolMem can cite or identify page numbers.

Don't add OCR initially.

If a PDF has:

```
25 pages
<100 characters extracted
```

mark:

```
extraction_quality = low
possible_scanned_pdf = true
```

and let the user explicitly request OCR later.

---

### PPTX

`python-pptx` exposes text through each shape's `text_frame`, paragraphs and runs, and supports identifying text-containing shapes and tables.

Extract:

```
=== SLIDE 1 ===
Title
Body
Table text...

=== SLIDE 2 ===
...
```

Excellent for schoolMem questions.

---

### DOCX

Use local document parsing and retain:

```
headings
paragraphs
table text
```

No Claude call.

---

# 14. Search strategy

Start with SQLite FTS5.

Example:

```
achios-canvas search \
  --course STINTSY \
  --query '"cross validation"' \
  --limit 6 \
  --json
```

Internally:

```
SELECT
    d.id,
    d.title,
    d.source_type,
    snippet(documents_fts, 1, '', '', ' … ', 40) AS snippet,
    bm25(documents_fts) AS score
FROM documents_fts
JOIN documents d ON d.id = documents_fts.rowid
WHERE documents_fts MATCH ?
  AND d.course_id = ?
ORDER BY score
LIMIT 6;
```

That already supports a lot more semantic variation than plain `grep`, because FTS offers terms, phrases, prefixes and ranking.

## Only consider embeddings if you see actual failures

For example, if:

> “How does the professor explain overfitting?”

fails because the slides only say:

> “model memorizes noise”

then hybrid semantic retrieval may eventually help.

Don't pay that complexity tax before observing it.

---

# 15. The `achios-canvas` JSON contract

This is one of the most important components for token efficiency.

Every command should have two modes:

```
human output
--json
```

And ideally:

```
--detail
```

for progressive disclosure.

### `status`

```
achios-canvas status --json
```

```
{
  "auth": "ok",
  "last_successful_sync": "2026-09-07T17:30:00+08:00",
  "stale": false,
  "courses": 6,
  "partial_courses": []
}
```

### `due`

```
achios-canvas due --days 7 --json
```

```
{
  "fresh_at": "2026-09-07T17:30:00+08:00",
  "timezone": "Asia/Manila",
  "items": [
    {
      "course": "STINTSY",
      "assignment_id": 123,
      "title": "Model Evaluation",
      "due_at": "2026-09-09T23:59:00+08:00",
      "state": "unsubmitted",
      "missing": false
    }
  ]
}
```

Don't include the 5,000-character assignment description.

---

### `assignment`

```
achios-canvas assignment 123 --json
```

This can contain the detailed description.

---

### `grades`

```
achios-canvas grades --course STINTSY --json
```

---

### `announcements`

```
achios-canvas announcements \
  --course STINTSY \
  --days 14 \
  --limit 10 \
  --json
```

---

### `search`

```
achios-canvas search \
  --course STINTSY \
  --query "neural network dropout" \
  --limit 5 \
  --json
```

---

### `files`

```
achios-canvas files find \
  --course STINTSY \
  --query "lecture 5" \
  --json
```

---

### `files fetch`

```
achios-canvas files fetch 76532 --json
```

---

### `files copy-to-schoolmem`

```
achios-canvas files copy-to-schoolmem 76532 --json
```

No path argument.

That's intentional.

Claude should **not** supply:

```
--dest /wherever/claude/decides
```

The subject mapping controls it.

---

# 16. Token architecture: I'd target closer to 98% deterministic operations

The earlier 90–95% estimate was conservative.

For routine operations, I would target:

|Workflow|Script|LLM|
|---|---|---|
|Periodic Canvas sync|100%|0%|
|Discover new assignment|100%|0%|
|Deadline comparison|100%|0%|
|Submission-state detection|100%|0%|
|Grade change detection|100%|0%|
|Announcement detection|100%|0%|
|File discovery|100%|0%|
|File download|100%|0%|
|PDF/PPTX extraction|100%|0%|
|Full-text search|100%|0%|
|Telegram notification|100%|0%|
|Interpret arbitrary user wording|—|LLM|
|Explain/synthesize course material|retrieval|LLM|
|Make a study strategy|structured facts|LLM|

The goal isn't really “95% versus 5% by lines of code.”

The useful metric is:

> **How many Canvas-related model invocations happen without Aki asking a question?**

The answer should be:

# **Zero.**

---

# 17. schoolMem tool-use strategy

The schoolMem model should follow a small decision tree:

```
User message
    │
    ├── factual Canvas state?
    │      due / submitted / grades / announcements
    │             │
    │             └── call compact structured command
    │
    ├── looking for material/file?
    │             │
    │             └── files/search command
    │
    ├── content question?
    │             │
    │             └── FTS search → top 3-6 snippets
    │
    └── broad synthesis?
                  │
                  └── retrieve more only as needed
```

## Example

> What do I have due tomorrow?

LLM gets:

```
{
  "items": [
    {
      "course": "CCPROG",
      "title": "Exercise 4",
      "due": "2026-09-08T23:59:00+08:00",
      "state": "unsubmitted"
    }
  ]
}
```

Maybe 50–100 tokens.

---

> Explain the professor's discussion of regularization.

Search returns:

```
{
  "results": [
    {
      "source": "Lecture 7.pdf",
      "page": 18,
      "snippet": "Regularization adds..."
    },
    {
      "source": "Lecture 7.pdf",
      "page": 19,
      "snippet": "L1 penalties..."
    }
  ]
}
```

Then Claude explains.

This is what keeps the cost low.

---

# 18. achiSchooNounce integration is already mostly solved

Your existing `email_digest.py` explicitly routes the DLSU account to `telegram_school.env`, and it has both an LLM synthesis path and a deterministic `--raw` mode.

Even better, `telegram_notify.py` already says scheduled jobs should import its shared `send()` implementation rather than creating another sender. It centralizes credentials, Telegram's 4096-character splitting, token redaction, retryable status codes, and `retry_after` behavior.

Canvas should simply:

```
from telegram_notify import send

send(message, env_path=CONFIG_DIR / "telegram_school.env")
```

No new bot.

---

# 19. Event model

I strongly recommend the `schoolbridge` pattern here.

Its event watcher has stable event types for things such as:

```
new_assignment
due_date_changed
grade_posted
grade_changed
new_announcement
```

and is designed around comparing persisted previous state with current state.

Your v1 events:

```
new_assignment
assignment_changed
due_date_changed

new_announcement

grade_posted
grade_changed

auth_expired
auth_restored

sync_partial
```

Don't initially notify:

```
page_changed
module_changed
file_changed
```

unless you find that useful.

They can still be recorded.

---

# 20. Silent baseline

Initial import must do:

```
Canvas currently has:
48 assignments
74 announcements
62 files
...
```

and generate:

```
0 notifications
```

Set:

```
baseline_complete = true
```

Afterwards, only new changes produce events.

Otherwise installing Canvas sync will spam achiSchooNounce with an entire semester.

---

# 21. Event fingerprints

Example:

```
event:
due_date_changed

fingerprint:
sha256(
  "due_date_changed" +
  course_id +
  assignment_id +
  old_due_at +
  new_due_at
)
```

UNIQUE constraint prevents duplicate notifications.

This means re-running after a crash is safe.

---

# 22. Notification examples

New assignment:

```
📚 STINTSY

New assignment
Model Evaluation Exercise

Due: Wed, Sep 9 · 11:59 PM
Status: Not submitted
```

Due-date change:

```
📚 CCPROG

Deadline changed
Machine Project 2

Sep 10 · 11:59 PM
→ Sep 12 · 11:59 PM
```

Grade:

```
📚 STINTSY

Grade posted
Model Evaluation Exercise

92 / 100
```

Authentication:

```
🔐 Canvas authentication expired

Last successful sync:
Sep 7 · 5:30 PM

Your saved school data is still available,
but new Canvas information cannot be retrieved
until the Canvas session is refreshed.
```

No LLM required.

---

# 23. Stale-data behavior

This deserves explicit UX.

Suppose Canvas authentication dies Monday.

On Tuesday you ask:

> What is due this week?

schoolMem should still answer:

```
I have 3 saved deadlines this week:
...

Canvas data was last successfully synced Monday at 8:30 PM,
so newer changes may be missing.
```

Do **not** return:

```
Canvas unavailable.
```

The entire reason for a local knowledge base is graceful degradation.

---

# 24. Gmail/Canvas deduplication

Your current DLSU email categorizer deliberately treats Canvas/Instructure/assignment/quiz/submission messages as academic email.

So after Canvas becomes stable:

```
                    Canvas healthy?
                    /             \
                  yes              no
                  /                 \
 Canvas API authoritative        Gmail remains fallback
 for Canvas-generated notices
```

I'd delay this until production Canvas has worked reliably for maybe several days.

Then suppress known automated Canvas notification emails only if:

```
last Canvas sync < configured freshness threshold
AND
auth_state == OK
```

Do not suppress professor/registrar/HDA email.

---

# 25. Proposed implementation phases

## Phase 0 — Close remaining uncertainty

Goal:

```
Know actual session behavior
Know actual subjects
Know actual raw paths
```

No production jobs yet.

---

## Phase 1 — Read-only data foundation

Deliver:

```
CanvasClient
SQLite store
courses
assignments
submissions
grades
announcements
```

At the end of this phase:

```
achios-canvas due --days 7
achios-canvas grades
achios-canvas announcements
```

should work locally.

---

## Phase 2 — Course knowledge ingestion

Add:

```
modules
pages
file discovery
file downloads
text extraction
FTS5
```

At the end:

> “Find the lecture discussing regularization.”

works.

---

## Phase 3 — Telegram integrations

Add:

```
change events
achiSchooNounce
schoolMem CLI guidance
copy-to-raw
```

---

## Phase 4 — Reliability

Add:

```
systemd timer
stale state
auth notification dedupe
partial failure
telemetry/status
email dedupe
```

---

## Phase 5 — Optional

Only after everything else:

```
discussion replies
remote Ubuntu MFA login
semantic/vector search
MCP
```

---

# 26. Recommended ticket graph

I would use the existing #24 as the parent epic rather than turning it into one giant coding PR.

```
#24 Canvas integration epic
 │
 ├─ A. Measure DLSU Canvas session lifetime
 ├─ B. Audit schoolMem routing and subject mappings
 │
 ├─ C. Build hardened Canvas cookie HTTP client
 ├─ D. Add Canvas SQLite storage schema
 │
 ├─ E. Sync courses, assignments, submissions and grades
 ├─ F. Sync announcements
 │
 ├─ G. Sync modules and pages
 ├─ H. Add resilient file discovery
 ├─ I. Add secure file downloader and cache
 │
 ├─ J. Extract course documents and build FTS index
 ├─ K. Build achios-canvas query CLI
 │
 ├─ L. Add Canvas event/diff engine
 ├─ M. Send Canvas events to achiSchooNounce
 ├─ N. Integrate schoolMem interactive Canvas queries
 ├─ O. Add safe copy-to-schoolMem raw
 │
 ├─ P. Add scheduled sync, stale state and observability
 ├─ Q. Deduplicate Canvas notification emails
 │
 ├─ R. Optional discussion sync
 └─ S. Optional protected reauthentication flow
```

Dependencies:

```
A ────────┐
B ────────┼─> C -> D -> E -> K -> N
          │        │    │
          │        │    ├-> F
          │        │    ├-> G -> H -> I -> J -> K
          │        │    └-> L -> M
          │        │
          │        └-----------------> O
          │
          └--------------------------> P

P + M -> Q

R optional after G
S optional only after A demonstrates need
```

---

# 27. Ready-to-create GitHub tickets

Below is the set I would actually use.

# Parent: #24 — DLSU Canvas sync into schoolMem and achiSchooNounce

Use #24 as the parent tracking issue. Do not implement the full integration in one PR. Child tickets below should link back to #24 and update its checklist as they land.

---

## Ticket A — Measure DLSU Canvas session lifetime and refresh behavior

### Goal

Measure how long the existing browser-derived Canvas session remains usable by Ubuntu and determine whether Canvas responses refresh or replace relevant cookies.

### Scope

- Continue using the private cookie/session material under `~/.config/achios/canvas/`.

- Use the persistent domain-aware cookie jar from the current experiment.

- Probe one fixed low-risk authenticated Canvas endpoint.

- Record only redacted metadata:

    - timestamp

    - HTTP status

    - response class: valid JSON / redirect / HTML / error

    - whether response cookies were set

    - cookie names changed, never cookie values

- Observe at:

    - immediate

    - approximately 1 hour

    - overnight

    - approximately 24 hours

    - optionally later intervals if still authenticated

- Confirm whether Google login + MFA is required again after expiry.


### Do not

- Log Cookie headers.

- Store session values in Git.

- Assume requests extend the session lifetime.

- Attempt automated Google login.


### Acceptance criteria

- At least immediate, 1-hour, overnight and 24-hour results are recorded, unless authentication expires earlier.

- Expiry is demonstrated through actual request behavior rather than cookie metadata alone.

- We know whether response cookies change during successful reads.

- Failure state clearly identifies whether manual reauthentication is required.

- Existing Canvas session credentials remain private.


### Tests

No production unit test requirement; redacted probe code should not expose credentials in stdout/stderr.

### Dependency

None.

---

## Ticket B — Audit schoolMem routing, vault rules and Canvas course mappings

### Goal

Determine the exact integration points for schoolMem and the approved destination path for each selected Canvas course.

### Scope

- Inspect current achiCore ownership of the schoolMem Telegram topic.

- Inspect the schoolMem Telegram working directory and prompt/routing configuration.

- Inspect unattended vault write guards.

- Verify whether `wiki/`, `inbox/`, subject directories and `raw/` directories have separate write rules.

- Enumerate active Canvas courses.

- Ask Aki to select the courses to synchronize if not already selected.

- Map each selected Canvas course ID to:

    - alias

    - subject key

    - verified existing schoolMem subject directory

    - verified raw destination

- Store machine-specific mapping outside Git under:

    - `~/.config/achios/canvas/config.json`


### Example config

```
{
  "timezone": "Asia/Manila",
  "courses": {
    "123456": {
      "enabled": true,
      "alias": "STINTSY",
      "subject_key": "stintsy",
      "schoolmem_raw": "/verified/path/to/STINTSY/raw"
    }
  }
}
```

### Safety requirements

- Never guess a subject path from the Canvas course title.

- Never auto-create arbitrary vault locations.

- Canvas sync must not automatically promote content into `wiki/`.

- Paths must be canonicalized before use.


### Acceptance criteria

- Current routing is documented.

- At least one Canvas course has a verified mapping.

- Config parser rejects nonexistent or unsafe raw paths.

- No Canvas session credentials are stored with course mappings.


### Dependency

None.

---

## Ticket C — Build hardened read-only Canvas cookie HTTP client

### Goal

Replace temporary `/tmp` experiments with a reusable production Canvas HTTP client.

### Proposed file

`scripts/canvas_client.py`

### Required capabilities

- Fixed origin: `https://dlsu.instructure.com`.

- Load private session/cookie jar.

- Persist response cookie changes safely.

- GET-only public interface.

- Manual redirect handling.

- XSSI-prefix stripping (`while(1);`).

- JSON content validation.

- Login-page/redirect detection.

- Canvas `Link` header pagination.

- Timeout handling.

- Bounded retries.

- 429 handling.

- Rate-limit header recording.

- Typed exceptions.


### Error classes

- `CanvasAuthExpired`

- `CanvasPermissionDenied`

- `CanvasNotFound`

- `CanvasRateLimited`

- `CanvasTransientError`

- `CanvasInvalidResponse`

- `CanvasDownloadError`


### Authentication rules

A `403` alone must not be interpreted as authentication expiry.

When useful, distinguish permission failure by probing a known authenticated endpoint.

### Redirect security

- Canvas credentials may only be attached to the configured Canvas origin.

- External redirect destinations must never receive Canvas cookies.

- Reject unexpected schemes.


### Logging

Allowed:

```
GET /api/v1/courses → 200 application/json
request cost=0.21
```

Forbidden:

```
Cookie: ...
Set-Cookie: ...
authenticated URL containing credentials
```

### Acceptance criteria

- Authenticated course API request works through this client.

- Pagination is proven with a fixture containing multiple pages.

- XSSI-prefixed JSON parses.

- Login HTML produces `CanvasAuthExpired`.

- Permission 403 remains distinguishable from auth expiry.

- External redirect test proves Canvas cookie is not forwarded.

- Session updates persist without logging values.


### Tests

Unit tests for:

- XSSI

- redirect/login detection

- 401

- legitimate 403

- 404

- 429

- malformed JSON

- Link pagination

- retry limits

- credential redaction

- host restrictions


### Dependencies

Ticket A informs production expectations but does not have to fully finish before development starts.

---

## Ticket D — Add local Canvas SQLite storage and migration layer

### Goal

Create the canonical local structured knowledge store.

### Proposed files

- `scripts/canvas_store.py`

- `scripts/canvas_schema.sql`


### Location

`~/.local/share/achios/canvas/canvas.db`

### Tables

Initial:

- `courses`

- `assignments`

- `assignment_dates`

- `submissions`

- `enrollments`

- `announcements`

- `sync_runs`

- `sync_course_status`

- `events`


Later-compatible:

- `modules`

- `module_items`

- `pages`

- `files`

- `documents`

- `documents_fts`


### Requirements

- SQLite foreign keys enabled.

- Schema version table.

- Migrations are forward-only and repeatable.

- UPSERT on stable Canvas IDs.

- Timestamps stored in ISO 8601 UTC or normalized datetime representation.

- Display/query conversion happens using configured timezone.

- Write operations use transactions.

- A failure in one course must not erase previous good data for other courses.

- Optional raw JSON may be retained for debugging but is not the query interface.


### Acceptance criteria

- Empty DB initializes automatically.

- Second initialization does not modify valid schema.

- Re-upserting an identical object produces no duplicate.

- Changed object updates correctly.

- Partial-course rollback preserves previous committed data.

- Schema version is queryable.


### Tests

- initialization

- migrations

- duplicate upsert

- changed entity

- FK behavior

- rollback

- crash-safe transaction behavior


### Dependency

Ticket C.

---

## Ticket E — Sync courses, assignments, personal submissions and grades

### Goal

Implement the highest-value CanvasFacts data.

### Proposed file

`scripts/canvas_sync.py`

### Endpoints/data

For each enabled course:

- course metadata

- assignments

    - include current submission

    - include all dates/overrides

- personal enrollment/grade information


### Assignment fields

Persist at minimum:

- Canvas ID

- course ID

- name

- effective `due_at`

- unlock/lock dates

- points possible

- grading type

- updated timestamp

- source URL

- description HTML/text


### Submission fields

Persist:

- workflow state

- attempt

- submitted timestamp

- score

- grade

- late

- missing

- excused

- graded timestamp

- late-policy status


### Deadline behavior

The CLI/query layer should calculate date windows itself using the configured timezone.

Do not use a Canvas calendar feed.

### Acceptance criteria

For a sampled course:

- assignment count matches paginated Canvas data

- sampled due dates match visible Canvas

- sampled submission state matches Canvas

- sampled personal grade fields match visible Canvas

- second sync creates no duplicate rows

- assignment updates replace the previous value

- failure for one course preserves previous good course data


### Tests

- assignment pagination

- student override/effective due-date fixture

- submitted

- unsubmitted

- missing

- late

- excused

- changed due date

- grade appears

- grade changes

- partial course failure


### Dependencies

Tickets B, C, D.

---

## Ticket F — Sync Canvas announcements

### Goal

Store course announcements deterministically for querying and notifications.

### Requirements

- Fetch announcements for enabled courses.

- Store context/course mapping.

- Preserve:

    - ID

    - title

    - message HTML

    - normalized text

    - author when visible

    - posted time

    - source URL

- Follow pagination.

- Do not mark announcements read as part of sync.


### Acceptance criteria

- Sampled announcements match Canvas.

- Repeated sync has no duplicates.

- A newly injected fixture creates exactly one new stored announcement.

- Updated content updates existing row.


### Tests

- pagination

- HTML normalization

- duplicate suppression

- multiple course context codes

- partial permission failure


### Dependencies

Tickets C, D.

---

## Ticket G — Sync modules and Canvas Pages

### Goal

Capture course structure and text content not represented in assignments/files.

### Requirements

Modules:

- Fetch module list with `include[]=items` and `include[]=content_details`.

- If Canvas omits module items, fetch module items separately.

- Preserve module and module-item ordering.

- Track File/Page/Assignment/Discussion/etc. item types.


Pages:

- List pages.

- Fetch body for new/changed pages.

- Normalize HTML to text/Markdown.

- Preserve source URL and update timestamp.


### Acceptance criteria

- Module ordering matches Canvas.

- A module fixture with omitted inline items triggers separate item retrieval.

- Page text is searchable locally.

- Unchanged page bodies are not unnecessarily rewritten.


### Tests

- module pagination

- omitted items fallback

- item types

- changed page

- deleted/unavailable page behavior

- malformed HTML


### Dependencies

Tickets C, D.

---

## Ticket H — Add resilient Canvas file discovery

### Goal

Discover student-visible course files even when `/courses/:id/files` is forbidden.

### Discovery sources

1. course Files API

2. module File items

3. Canvas file links in Page bodies

4. assignment descriptions

5. announcements

6. syllabus when exposed

7. optional discussions later


### Requirements

- Deduplicate by Canvas file ID.

- Store how each file was discovered.

- A 403 on course Files listing means `listing_forbidden`, not `course_has_no_files`.

- Resolve module `content_id` to file metadata when necessary.

- Parse only Canvas-local file references automatically.

- External links may be indexed as links but are not automatically downloaded.


### Acceptance criteria

- A test course with Files API=403 still discovers module files.

- Embedded `/files/{id}` links are discovered.

- One file referenced from multiple sources produces one file record with multiple provenance links or equivalent provenance representation.

- Empty course remains distinguishable from failed file listing.


### Tests

- Files 200

- Files 403

- module File item

- duplicate file references

- page links

- assignment links

- announcement links

- malformed links


### Dependencies

Tickets C, D, G.

---

## Ticket I — Add secure file downloader and local cache

### Goal

Reliably download Canvas-protected files without leaking cookies or accepting login/error HTML as course content.

### Proposed file

`scripts/canvas_download.py`

### Cache location

`~/.local/share/achios/canvas/cache/<course-id>/<file-id>/`

### Download algorithm

- Resolve Canvas metadata.

- Download to `.part`.

- Manually follow redirects.

- Attach Canvas credentials only on approved Canvas origin.

- Strip credentials before external redirects.

- Validate content.

- Hash SHA-256.

- Atomically rename to final filename.

- Update `files` DB record.


### Validation

For all files:

- nonzero size

- no login HTML masquerading as successful response

- metadata size comparison where available


For PDFs:

- `%PDF-` magic


For Office documents:

- plausible ZIP/OOXML signature


### File names

Sanitize:

- `/`

- `\`

- null bytes

- `..`

- control characters


Prevent:

- path traversal

- symlink escape


### Acceptance criteria

- Existing known Canvas PDF downloads and validates.

- Unauthenticated login HTML is rejected.

- External redirected request receives no Canvas cookie.

- Interrupted download leaves no completed corrupt file.

- Existing identical hash does not redownload unnecessarily unless forced.


### Tests

- valid PDF

- HTML login response

- size mismatch

- external redirect

- redirect loop

- unsafe filename

- existing file

- `.part` cleanup


### Dependencies

Tickets C, D, H.

---

## Ticket J — Extract Canvas/course documents and build FTS5 search index

### Goal

Make saved course material searchable without an LLM or vector database.

### Proposed file

`scripts/canvas_extract.py`

### Supported v1 sources

- Canvas pages

- assignments

- announcements

- PDF

- PPTX

- DOCX


### Extraction format

Preserve structural boundaries:

PDF:

```
=== PAGE 1 ===
...
```

PPTX:

```
=== SLIDE 1 ===
...
```

### Database

Add:

- `documents`

- FTS5 virtual table `documents_fts`


### Requirements

- Extraction happens only when the content hash changes.

- Store extraction status and errors.

- Very-low-text PDFs should be marked as possible scanned documents rather than silently treated as empty.

- No OCR in v1.

- No embedding API.

- No LLM preprocessing.


### Search result

Return:

- course

- title

- source type

- source ID

- page/slide when recoverable

- short snippet

- source path/URL

- relevance score


### Acceptance criteria

- Known phrase in PDF is found.

- Known phrase in PPTX is found.

- Canvas page content is found.

- Changed file is re-extracted.

- Unchanged file is skipped.

- Search requires zero LLM calls.


### Tests

- PDF extraction

- PPTX extraction

- DOCX extraction

- HTML normalization

- FTS ranking

- phrase query

- changed hash

- extraction failure


### Dependencies

Tickets D, G, I.

---

## Ticket K — Build `achios-canvas` deterministic query CLI

### Goal

Provide the single stable interface used by schoolMem and shell workflows.

### Proposed commands

```
achios-canvas status
achios-canvas courses

achios-canvas due
achios-canvas assignments
achios-canvas assignment

achios-canvas grades

achios-canvas announcements

achios-canvas search

achios-canvas files find
achios-canvas files fetch
achios-canvas files copy-to-schoolmem
```

### Requirements

- Human-readable output by default.

- Stable `--json`.

- JSON output goes to stdout.

- Diagnostics go to stderr.

- Predictable exit codes.

- `--detail` for verbose content.

- Default responses remain compact.

- All answers include freshness metadata when relevant.


### Example

```
achios-canvas due --days 7 --json
```

must not emit full assignment descriptions.

### Exit codes

Suggested:

```
0 success
2 invalid arguments
3 stale but usable
4 authentication required
5 partial data
6 not found
7 permission denied
8 internal/storage error
```

### Acceptance criteria

- Example schoolMem questions can each be answered with one or two CLI calls.

- Compact JSON avoids unnecessary large text.

- Stale state is explicit.

- Commands never print credentials.


### Tests

Contract snapshots for each command.

### Dependencies

Tickets E, F, J.

---

## Ticket L — Add deterministic Canvas event/diff engine

### Goal

Detect meaningful Canvas changes without LLM calls.

### Proposed file

`scripts/canvas_events.py`

### V1 events

- `new_assignment`

- `due_date_changed`

- `assignment_changed`

- `new_announcement`

- `grade_posted`

- `grade_changed`

- `auth_expired`

- `auth_restored`

- `sync_partial`


### Behavior

- First successful import is a silent baseline.

- Later imports compare previous authoritative values.

- Events have stable deduplication fingerprints.

- Re-running the same state does not produce another event.

- Failed/partial syncs must not generate fake deletions.


### Acceptance criteria

- Initial import generates no user-facing events.

- New assignment fixture produces one event.

- Re-running produces zero duplicate events.

- Due-date move produces one `due_date_changed`.

- First grade produces `grade_posted`.

- Revised grade produces `grade_changed`.

- Partial course failure does not imply entities were deleted.


### Tests

All above event scenarios plus crash/restart replay.

### Dependencies

Tickets D, E, F.

---

## Ticket M — Send selected Canvas events to achiSchooNounce

### Goal

Use the existing Telegram notification infrastructure for proactive Canvas changes.

### Requirements

- Reuse `scripts/telegram_notify.py`.

- Use `~/.config/achios/telegram_school.env`.

- Do not create a separate bot library.

- Format messages deterministically.

- Mark event notified only after successful Telegram send.

- Retry behavior remains owned by `telegram_notify.py`.


### Notify initially

- new assignment

- due-date change

- new announcement

- grade posted/changed

- authentication expired/restored


### Do not notify initially

- every new file

- every page edit

- every module edit

- discussions


### Acceptance criteria

- Each supported event has a clear Telegram format.

- Duplicate event does not send twice.

- Failed Telegram send leaves event pending.

- Credentials never enter Canvas logs.


### Tests

Mock shared sender.

### Dependencies

Tickets L and existing `telegram_notify.py`.

---

## Ticket N — Integrate Canvas queries into schoolMem Telegram

### Goal

Teach the existing schoolMem Claude session to use `achios-canvas` as the authoritative Canvas retrieval layer.

### Routing policy

For factual Canvas questions:

```
query CLI first
```

For course-content questions:

```
search CLI
→ retrieve top passages
→ reason using those passages
```

### Examples

```
What is due this week?
→ achios-canvas due --days 7 --json
```

```
Have I submitted everything tomorrow?
→ achios-canvas due --from ... --to ... --json
```

```
What is my grade in STINTSY?
→ achios-canvas grades --course STINTSY --json
```

```
What does Lecture 5 say about PCA?
→ achios-canvas search --course STINTSY --query "PCA" --limit 5 --json
```

### Token rules

- Never load the full Canvas database into model context.

- Never dump raw API payloads.

- Default retrieval limit 5 or lower.

- Expand only if first retrieval is insufficient.

- No nested LLM call from Canvas scripts.

- Canvas facts come from deterministic commands.


### Vault rules

Do not modify wiki policy simply to support Canvas.

### Acceptance criteria

- Example questions in parent issue work.

- Freshness is communicated when Canvas data is stale.

- Normal factual query needs only compact CLI output.

- Canvas integration causes zero additional background LLM calls.


### Tests

Prompt/tool-routing tests where available; otherwise scripted manual acceptance suite.

### Dependencies

Tickets B and K.

---

## Ticket O — Add safe Canvas file copy into mapped schoolMem `raw/`

### Goal

Support:

> "Download Lecture 5 into STINTSY."

without letting the model choose arbitrary filesystem paths.

### Command

```
achios-canvas files copy-to-schoolmem FILE_ID
```

### Requirements

- Resolve course from file record.

- Resolve destination only through verified course mapping.

- Canonicalize destination.

- Verify it remains inside approved `raw/`.

- Reject symlinks escaping the approved directory.

- Download/cache first when needed.

- Validate file before copying.

- Never overwrite unrelated existing file silently.

- Collision policy:

    - same hash → report already present

    - different hash/same name → deterministic safe renamed file or explicit conflict

- Return final path and hash.


### Acceptance criteria

- Known PDF copies to correct verified course folder.

- File for unmapped course fails safely.

- `../` traversal is impossible.

- Symlink escape fixture fails.

- Existing same file is idempotent.

- Existing different file is preserved.


### Dependencies

Tickets B, I, K.

---

## Ticket P — Add systemd Canvas sync timer, stale state and operational status

### Goal

Run the sync safely without a permanent daemon.

### Components

- `achios-canvas-sync.service`

- `achios-canvas-sync.timer`


### Suggested initial frequency

Every 30 minutes.

This interval is for freshness only and must not be described as extending Canvas authentication lifetime.

### Service behavior

- oneshot

- bounded runtime

- lock to prevent overlapping runs

- journald logs

- no secret output

- nonzero exit for full failure

- distinguish partial/stale state

- preserve previous data


### Stale behavior

On auth expiry:

- stop protected live sync

- preserve DB/cache

- mark auth state expired

- send one auth notification

- do not repeatedly spam every 30 minutes

- interactive queries continue against cache


### Status command

```
achios-canvas status
```

shows:

- auth state

- last attempt

- last successful sync

- stale age

- partial courses

- last error class


### Acceptance criteria

- Timer runs correctly.

- Concurrent invocation is blocked.

- Expired session generates one notification.

- Subsequent timer runs do not flood.

- Auth restoration clears stale state.

- Existing data survives repeated failures.


### Dependencies

Tickets C, D, L, M.

---

## Ticket Q — Deduplicate direct Canvas events from DLSU email digest

### Goal

Prevent duplicate achiSchooNounce messages when Canvas API and Gmail describe the same automated Canvas event.

### Prerequisite

Do not implement until direct Canvas sync has demonstrated adequate reliability.

### Policy

When Canvas is healthy and fresh:

- direct Canvas sync owns:

    - assignments

    - Canvas announcements

    - submission notifications

    - grade events


Gmail continues to own:

- professor/direct messages

- registrar

- thesis/admin messages

- HDA/emergency notices

- other DLSU mail


When Canvas is stale/auth-expired:

- automated Canvas email may remain available as fallback.


### Requirements

- Add explicit detector for Canvas-generated automated mail.

- Suppression must depend on Canvas health/freshness.

- Do not broadly suppress all mail containing the word "Canvas".

- No LLM required for deduplication.


### Acceptance criteria

- Automated duplicate is suppressed when Canvas healthy.

- Same message is retained when Canvas stale.

- Direct professor email is never suppressed.

- HDA/registrar behavior unchanged.


### Dependencies

Ticket P plus a proven stability period.

---

## Ticket R — Optional: sync visible Canvas discussions and replies

### Goal

Provide best-effort discussion search without delaying core Canvas delivery.

### Scope

- topic metadata

- opening post

- visible top-level entries

- visible replies if accessible

- group-discussion behavior

- required-initial-post detection


### Rules

- Read-only.

- Never post to unlock replies.

- Never change read state merely to unlock data.

- `require_initial_post` is a permission/availability state, not a failure.

- Discussions must not make the overall course sync fail.


### Acceptance criteria

- Accessible topic is stored.

- Visible replies are stored.

- Required-initial-post returns `restricted` without posting.

- Group-inaccessible content is skipped safely.

- Discussion failure does not affect assignments/grades/etc.


### Dependency

Core integration completed first.

### Priority

Low / optional.

---

## Ticket S — Optional: investigate protected Ubuntu reauthentication from Telegram

### Goal

Only if measured session lifetime makes manual cookie refresh excessively frequent, investigate a safer interactive way for Aki to refresh Ubuntu's Canvas session.

### Scope

Research/prototype only:

```
Telegram
→ protected private URL
→ interactive browser session actually running on Ubuntu
→ DLSU Canvas
→ Google SSO
→ MFA
→ resulting Canvas cookies remain on Ubuntu
```

### Requirements

- Do not automate credentials.

- Do not automate MFA.

- Do not expose browser session publicly.

- Strong authentication/access restriction around remote browser.

- Resulting Canvas session stored in existing private session location.

- Test whether Google accepts the browser environment.


### Explicit non-goal

No autonomous Google-login agent.

### Decision gate

Do not build if Ticket A shows reauthentication is infrequent enough that private manual session refresh is acceptable.

### Acceptance criteria

Either:

1. protected interactive login is proven securely, or

2. experiment is documented as unsuitable and current manual method remains the supported workflow.


### Dependency

Ticket A and production integration.

### Priority

Optional.

That ticket split would let you make small PRs instead of a single large change where cookie security, syncing, notifications, vault writes, and knowledge retrieval all become entangled.

# 28. Recommended PR grouping

I would not necessarily make one PR per ticket. I would use roughly:

|PR|Tickets|
|---|---|
|**PR 1 — Canvas client foundation**|C + basic tests|
|**PR 2 — Store + core CanvasFacts**|D + E + F|
|**PR 3 — Course content discovery**|G + H|
|**PR 4 — File cache**|I|
|**PR 5 — Knowledge search**|J + K|
|**PR 6 — Notifications**|L + M|
|**PR 7 — schoolMem integration**|N + O|
|**PR 8 — operations**|P|
|**PR 9 — email dedupe**|Q|
|Optional|R / S|

A and B are operational/research tickets and may not need conventional code PRs.

---

# 29. Tests I would insist on before calling this production-ready

There are a few I'd treat as release blockers:

```
AUTH
✓ XSSI JSON
✓ expired redirect
✓ 200 login HTML
✓ legitimate 403
✓ cookie persistence
✓ no credential leakage to external redirects

PAGINATION
✓ multi-page courses
✓ assignments
✓ announcements
✓ modules/pages/files

SYNC
✓ second run is idempotent
✓ changed entity updates
✓ partial course failure retains old data
✓ failure does not create fake deletion events

DATES
✓ Manila timezone
✓ Sunday/Monday boundary
✓ month/year boundary
✓ overridden assignment date
✓ null/undated assignment

FILES
✓ /files 403 fallback
✓ module file
✓ embedded file
✓ duplicate file ID
✓ corrupt PDF
✓ login HTML
✓ atomic .part handling
✓ path traversal
✓ symlink escape

EVENTS
✓ baseline silent
✓ new assignment
✓ moved due date
✓ grade posted
✓ grade changed
✓ no duplicate notification
✓ auth-expiry notification only once

KNOWLEDGE BASE
✓ page search
✓ PDF search
✓ PPTX search
✓ compact result limit
✓ stale-data indicator
```

---

# 30. A useful additional refinement: separate **freshness by subsystem**

Don't only have:

```
last_sync = ...
```

Have:

```
{
  "courses": "2026-09-07T17:30:00+08:00",
  "assignments": "2026-09-07T17:30:03+08:00",
  "grades": "2026-09-07T17:30:05+08:00",
  "announcements": "2026-09-07T17:30:07+08:00",
  "modules": "2026-09-07T17:30:19+08:00",
  "files": "2026-09-07T16:30:22+08:00"
}
```

Then if Files fails but assignments work:

> “Your deadline data is current as of 5:30 PM. File discovery for this subject is incomplete.”

That's far more accurate than marking the entire Canvas database stale.

---

# 31. I'd also separate **sync frequency by cost**

You don't need to recrawl everything every 30 minutes.

### Every 30 minutes

```
auth probe
courses lightweight metadata
assignments + submission
enrollment grades
recent announcements
```

### Every 2–6 hours

```
modules
page metadata
file metadata
```

### Only if changed/new

```
page bodies
file downloads
text extraction
FTS update
```

### On demand

```
large file
uncached file
optional discussion thread
```

This reduces Canvas traffic and disk churn while making the important user-facing facts fresh.

---

# 32. Token budget I would enforce

For schoolMem, I'd add actual limits.

### Factual commands

Target:

```
< 1,500 characters of JSON
```

whenever possible.

### Search

Default:

```
5 results
~500–800 characters/result maximum
```

Roughly:

```
2–4k tokens maximum retrieval
```

before the LLM.

### Expand-on-demand

Only make a second retrieval when needed.

So:

```
User
"What did the prof say about dropout?"
   │
   ▼
5 snippets
   │
   ├─ enough → answer
   │
   └─ insufficient
          │
          ▼
      document detail
```

not:

```
load every STINTSY document → Claude
```

This progressive-disclosure approach is also used by cookie-auth Canvas agent implementations specifically to prevent Canvas's very large native payloads from bloating model context.

---

# 33. One important nuance about Canvas assignments

I would **not rely heavily on Canvas's `bucket=upcoming` logic** for your main Telegram deadline feature.

Canvas supports buckets including `past`, `overdue`, `undated`, `ungraded`, `unsubmitted`, `upcoming` and `future`, but their exact semantics are not documented as clearly as the raw assignment/submission fields.

Since you want:

> “what is due this week”

we can make it more transparent:

```
effective_due_at >= week_start
AND effective_due_at < week_end
```

and separately display:

```
workflow_state
missing
late
submitted_at
```

That gives you predictable behavior independent of Canvas's bucket interpretation.

---

# 34. Priority order

If you want the shortest route to actual value, I would implement in this order:

**First:** C → D → E → F → K. At that point you already have a useful system capable of answering deadlines, submission state, grades and announcements.

**Second:** G → H → I → J. That makes schoolMem into the actual Canvas course knowledge base.

**Third:** L → M → N → O → P. That connects everything to Telegram and production scheduling.

**Later:** Q once reliability is proven.

**Optional only:** R and S.

The session-lifetime measurement A and mapping audit B can happen alongside the first implementation phase.

---

## Bottom line

The research changed one important recommendation: **I would use SQLite as the local source of truth, with FTS5 as the initial knowledge retrieval engine.** It's still very lightweight, but it removes a lot of awkwardness around JSON-file deduplication, change detection, grade/deadline queries and searchable document content. SQLite's native FTS capabilities are sufficient to defer embeddings/vector infrastructure until there is evidence you need semantic search.

The most important architectural boundary should remain strict:

> **Canvas → scripts → SQLite/files → compact deterministic query → Claude**
>
> not
>
> **Canvas → Claude → figure out what changed → another model → Telegram.**

That keeps scheduled operation at **zero LLM calls**, makes the integration usable even while Canvas auth is stale, and leaves Claude doing the part it is actually useful for: understanding your question, explaining course content, synthesizing several retrieved sources, and helping you study.
