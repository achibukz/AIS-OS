# 🔍 Architectural & Code Audit: TGDB Exporter & Self-Learning Loop

* **Date:** August 19, 2026
* **Target:** `docs/2026-08-18-feature-audit-tgdb-and-correction-harvester.md`
* **Auditor:** Claude Opus Deep Architecture Auditor
* **Branch:** `feat/correction-harvester`
* **Status:** Remediated & Documented

---

## 🚨 1. Executive Summary: Why the Self-Learning Loop was Broken

The **Autonomous Correction Harvester** (`scripts/extract_corrections.py`) was designed to turn user corrections, voice adjustments, and banned words into permanent system rules.

However, the self-learning loop suffered from **overly eager, naive regex pattern matching** that failed to distinguish between:
1. **Permanent system-level behavioral rules** (e.g. *"Always format tasks with checkboxes"*, *"Never use the word leverage"*).
2. **Transient conversational requests & one-off tasks** (e.g. *"Take note of this Google One subscription cancellation on Oct 13"*, *"Take note for the pitch submission form we need a pitch title"*, *"Change 'task' to 'also wait for austin's reply'"*).

### Consequences Observed
* **Pollution of `.agentrules`:** Day-to-day conversational commands, calendar instructions, and file edit requests were permanently appended into `.agentrules` and `decisions/log.md`.
* **System Prompt Bloat:** Because `.agentrules` is injected into every agent run, agents were forced to parse dozens of obsolete past conversation snippets.
* **Test Suite False Confidence:** Unit tests in `tests/test_extract_corrections.py` passed 100% (26/26 tests) because they only tested synthetic positive phrases (`"never use leverage"`), masking real-world conversational failures.

---

## 🛠️ 2. Detailed Root-Cause Breakdown

### A. Regex & Heuristic Flaws in `scripts/extract_corrections.py`
1. **Over-eager Directives (`take note`, `make sure` - L115–144):**
   * Regex: `r"(?:take note(?:\s+that|\s+on|\s*:|\s+of)?|make sure to|remember that|always make sure|rule:)\s*(.+)"`
   * Captures casual conversational phrases and tasks, classifies them into arbitrary domains (`tasks`, `voice`), and formats them as lifelong operational rules.
2. **Formatting Overrides (`change X to Y` - L150–171):**
   * Regex: `r"(?:change|update|replace)\s+(?:the\s+)?(.+?)\s+to\s+(.+)"`
   * Captures code editing instructions (e.g. *"change 'name of the cron' to 'just Email Debrief'"*) and treats them as permanent global overrides for all future chats.
3. **Banned Words Logic (L77–97):**
   * Enforces `len(word) > 2`, making it impossible to ban two-letter words (`"AI"`), while false-triggering on coding instructions (`"don't use the variable x"`).
4. **Brittle Deduplication (L177–193):**
   * Uses simple punctuation stripping and substring matching (`norm_rule in norm_corpus`), failing to detect semantic duplicates phrased slightly differently.

### B. Sanitization & Text Cleaner Leaks
1. **OpenAI Key Leaks (`scripts/tgdb_logger.py`):**
   * Secret redactor missed `sk-proj-*` and `sk-svc-*` patterns.
2. **Claude Text Cleaner (`scripts/export_transcripts.py`):**
   * Failed to strip `<thought>` / `<thinking>` tags and `<artifact>` blocks; lacked `re.IGNORECASE`.
3. **Antigravity JSON Dump Leaks:**
   * JSON tool execution payloads mixed with assistant responses were not stripped, leaking raw JSON logs into Obsidian notes.

### C. Pipeline & Synchronization Gaps
1. **Uncommitted AIS-OS Changes (`scripts/vault_inbox_sync.py`):**
   * `VAULTS` only tracked `schoolMem` and `achiMem`. When `extract_corrections.py` modified `.agentrules` and `decisions/log.md`, those files were left dirty and uncommitted in git.
2. **Debrief Hallucination Fallback (`scripts/evening_debrief.py`):**
   * If nothing was found in `decisions/log.md`, it fell back to scanning `tgdb/` directly, broadcasting unapplied or rejected candidate rules on Telegram as *"distilled into .agentrules today"*.

---

## 🏛️ 3. Formalized Architectural Rule: AI Model Allocation

```markdown
## AI Model Allocation & Workstream Roles
- **Auditing, Code Reviews & Feature Planning:** Use **Claude Opus** (or Claude 3.5 Sonnet / flagship reasoning) for exhaustive codebase audits, gap analysis, and system architecture planning.
- **Execution & Implementation:** Use **Gemini 3.7 Flash** (via Antigravity / agy) for fast execution, code changes, tool calls, debugging runs, and script builds.
```

* Registered in: `.agentrules`, `decisions/log.md`, `session-log.md`.
