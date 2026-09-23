# Canvas investigation checkpoint

The first-release design was approved on 2026-09-08. Use [the implementation plan](canvas-implementation-plan.md) and [the epic](https://github.com/achibukz/AIS-OS/issues/24) for current scope and ticket order. Two-hour sync, phone reauthentication and schoolWiki current-term selection are settled. The historical investigation below preserves live evidence; its earlier open decisions and JSON-store proposal are superseded.

# DLSU Canvas sync into schoolMem and achiSchooNounce

Ticket: https://github.com/achibukz/AIS-OS/issues/24

Status: live HTTP access and one PDF download verified on 2026-09-07. No integration deployed. Session lifetime remains unmeasured. Read the latest live checkpoint before resuming.

## Goal and agreed scope

Aki wants a simple personal integration for https://dlsu.instructure.com/. Sync announcements, assignments and due dates, files, pages, modules and personal grades. Discussion topics and visible replies are optional; Aki explicitly said not to add complex handling or delay the main integration for them. His account only. No calendar feed solution. Avoid building a large platform or an autonomous Google login workflow.

Expected Telegram requests:

- Show announcements for a subject.
- Show what is due this week, using assignment data rather than a calendar feed.
- Download a lecture PDF into that subject's raw folder in schoolMem.
- Answer questions about saved course data and personal grades.

Keep achiSchooNounce as the notification destination and schoolMem as the interactive query destination. Existing achiOS code uses `scripts/email_digest.py` for school announcements. achiCore owns the schoolMem topic. Inspect current routing and vault rules before implementation; do not assume a subject folder mapping.

## Evidence already obtained

Aki reported these live results in this task:

- Personal access token creation is unavailable.
- Opening https://dlsu.instructure.com/api/v1/courses?per_page=1 while logged in displays JSON.
- Canvas Course Downloader successfully downloaded the contents of one course. Aki described it as everything inside the course; individual content coverage has not been independently audited.
- Reauthentication requires Google login and MFA.
- Aki accepts storing a private Canvas session file on Ubuntu.
- Aki can open something from Telegram to perform authentication if necessary.
- Aki accepts using the working browser exporter while investigating access when his Mac is closed.

Agent checks found DLSU redirects through `/login/google` to Google. Chromium and a headless Chromium binary are cached on Ubuntu. No authenticated Ubuntu requests, PDF downloads, expiry measurements, or remote-login tests have run. No cookies have been collected. Do not report server sync as working.

## Recommended approach, conditional on tests

First try a small Python HTTP client using Canvas session cookies. The browser test establishes token-free API access, not API-free access. An HTTP client may reuse that session on Ubuntu without Playwright. Cross-machine acceptance and session lifetime remain unproven.

Keep the working course exporter as an initial import and fallback. If server requests work, use a scheduled sync on Ubuntu and a saved local dataset for Telegram queries. Use existing project storage conventions where possible; JSON plus files is sufficient for the first experiment. Do not introduce PostgreSQL, a dashboard, vector search, or a second bot framework without a demonstrated need.

Session refresh must preserve cookies returned by Canvas. Do not claim periodic reads defeat expiry. Canvas supports configurable session timeouts, and DLSU's effective policy is unknown. On expiry, retain saved data, mark it stale, and request reauthentication rather than looping through login attempts.

## Authentication from Telegram

Aki proposed opening a link from Telegram to authenticate the server. This is a candidate design, not tested behavior.

A plain Canvas link authenticates the phone browser, not the Ubuntu client. A working approach would need either a protected interactive view of a browser actually running on Ubuntu, or an explicit secure session transfer. Inspect existing remote-browser access before adding a service. Google may reject an automated or remote browser; test this before adopting it.

For the first experiment, a private transfer of Canvas-only cookies is acceptable to Aki. Never paste cookies, passwords, MFA codes, or authenticated request headers into chat, GitHub, logs, the vault, or Git. Keep session files outside the repository and web viewer, with owner-only permissions. Scope cookies to their original domains and do not forward a raw Cookie header to redirected download hosts.

## Next experiment

1. Resume with Aki and choose the existing secure transfer or server-browser method. Do not ask again whether a private session file on Ubuntu is acceptable; he already agreed.
2. Make a read-only course request from Ubuntu using that session. Record HTTP status, response type and counts, excluding credentials and private content.
3. For one chosen course, fetch an announcement, assignments with applicable due dates, personal grades, a discussion with visible replies, and one lecture PDF.
4. Verify the PDF is a real document rather than a login HTML response. Check its size or hash against the browser export where available.
5. Close the Mac and repeat from Ubuntu. Proposed observations are immediate, one hour, overnight and 24 hours. These are measurements to arrange, not an already scheduled monitor.
6. Record whether responses update cookies, when requests stop working, and whether Google plus MFA is required again. Never infer server-side validity from a cookie's expiry field alone.
7. If reuse works long enough, implement server sync. If it fails or expires too often, retain browser export/import and test protected interactive server login separately.

## Small implementation after the experiment

- Store course and content IDs, source URLs, content timestamps and last successful sync time. Follow pagination and discover files linked from modules and content, not only the Files listing.
- Keep downloads in a cache. Map Canvas course IDs to existing schoolMem subjects. Copy requested files to the verified raw folder without overwriting unrelated files.
- Use saved data for Telegram queries. Show freshness when stale. A missing uncached file requires a valid session; do not report it downloaded without checking the result.
- Derive weekly deadlines from assignments, including the user's applicable dates and submission state. Confirm week boundaries and timezone before shipping; Asia/Manila is a proposal.
- Fetch discussion topics and visible replies. Respect initial-post requirements and group access; do not post or mark content read to unlock it.
- Deduplicate changes and notifications. Initial backfill should not flood Telegram. Notify only on chosen changes or required authentication action.
- Treat permission failures, authentication expiry and partial fetches separately from an empty course. Preserve the last good data on failures.
- Use bounded retries for transient failures and rate limits. Re-running a sync should not duplicate files or records.

## Acceptance checks

- Ubuntu reads course data and downloads a verified PDF with the Mac closed, or records a clear failed experiment and keeps the browser fallback.
- Sampled announcements, deadlines and personal grades match the visible Canvas data. Discussion access is best effort and does not block delivery.
- A second sync creates no duplicate records or files.
- A partial failure preserves previous data and reports incomplete coverage.
- Session expiry produces a stale-data state and one actionable notification, without leaking credentials.
- schoolMem answers the example queries and copies the requested PDF into the correct subject raw folder.
- Automated tests cover pagination, duplicates, changed content, expiry, partial failures, safe file paths and date boundaries. Run each repository's prescribed tests for any implementation changes.
- Live evidence distinguishes user-reported browser success from agent-observed server success.

## Remaining decisions

- Secure session transfer method and whether an existing remote-browser service can support MFA from a phone.
- Actual session lifetime and acceptable reauthentication frequency.
- Selected courses, exact subject mappings, sync interval and initial backfill size.
- Whether to cache all PDFs or fetch most on demand, including a size limit.
- Which announcement, grade or deadline changes trigger notifications.
- Discussion reply scope. Aki requested initial topics and some classmates' replies; default proposal is all replies he can access for selected topics.

## References and alternatives

- [Canvas Course Downloader](https://github.com/jasp-nerd/canvas-course-downloader): working user-tested exporter. Uses session-authenticated API requests. Its documented student discussion export contains opening posts, so replies require a separate check.
- [Learning Agent Canvas Sync](https://github.com/zijinz456/learning-agent-canvas-extension): extension plus backend, useful reference for scheduled extraction. Its Python backend and PostgreSQL stack are more than the first experiment needs. Inspected content script uses credentialed fetch and handles 401; its discussion collector retrieves topics.
- [Canvas Student Data Export](https://github.com/davekats/canvas-student-data-export): main export requires a personal token. Cookie support for optional snapshots does not solve this task as supplied.
- [Canvas discussion endpoints](https://developerdocs.instructure.com/services/canvas/resources/discussion_topics): entries, replies and full-topic view. Verify permission-dependent behavior live.
- [Canvas session timeout source](https://github.com/instructure/canvas-lms/blob/master/app/middleware/sessions_timeout.rb): configurable timeout support; not proof of DLSU configuration.

Recommended executor: `claude-opus-4-6-thinking`, an existing registry key, because session handling, partial sync and retries can be wrong while passing narrow tests. Aki originally requested an Astra discussion; this document preserves that discussion and does not change a runtime model default.

## Live checkpoint, 2026-09-07

Aki transferred the Canvas Cookie header privately over SSH, replacing his first submission with a second. Ubuntu then fetched the course endpoint using Python urllib with redirects disabled. It returned HTTP 200 and a JSON list containing a course record. Cookies and course contents were not printed.

At 08:51:41 UTC, after Aki reported that Arc and his Mac were closed and he was using his phone, the same Ubuntu request again returned HTTP 200 with a valid course record. This verifies immediate server access independent of the Mac. It does not establish session lifetime, file downloads, discussion coverage or automatic reauthentication.

The private session is at `~/.config/achios/canvas/session.json`, outside the repository. Current probes use its Cookie header only for the fixed DLSU origin and refuse redirects. They do not yet persist response cookie updates. Next: verify one course and PDF, then measure session lifetime with a cookie jar that preserves domain scope and updates. No periodic monitor has been scheduled.

## Content checkpoint, 2026-09-07 at 08:56 UTC

Live Python HTTP probes returned 12 course records on the first page. Sampled endpoints returned announcements, assignments with submission data, and personal enrollment records. One discussion view returned 44 top-level entries. This verifies access, not complete pagination or grade-value correctness. Aki clarified that discussions and classmates' replies are optional and must not lead to extra engineering.

Several sampled Files listings returned 403. Another returned 13 files, with PowerPoint, Word and JPEG types. A further course exposed a PDF. A request without session cookies returned HTTP 200 with a non-PDF body and was rejected. The authenticated download through a domain-scoped cookie jar returned HTTP 200, application/pdf, a PDF header at byte zero and 632,460 bytes matching Canvas metadata. The sample is private at `~/.config/achios/canvas/sample.pdf`; nothing was copied into the vault.

The latest successful download was at 08:56:10 UTC, following the Mac-closed course check at 08:51:41 UTC. This is a short observation window, not an overnight expiry test. Probes now persist response cookies in a private Mozilla cookie jar. Temporary experiment scripts are under `/tmp/canvas-auth-ZFKIQ3lf/`; they are not production code and may disappear after reboot. Redacted receipts are stored beside the private session.

Next implementation should use a small HTTP client and existing Telegram integration. File discovery through modules or content links remains untested for courses whose listing returns 403. Confirm selected courses and subject mappings before a full import. No recurring job or expiry monitor has been installed.
