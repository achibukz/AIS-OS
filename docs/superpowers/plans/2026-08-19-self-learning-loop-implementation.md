# Self-Learning Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-optimized:subagent-driven-development` or `superpowers-optimized:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the self-learning audit report and the Hermes architecture findings to create a robust, self-learning loop for `achiAgy` (`@achiAgyOSBot`) and the Antigravity CLI / achiOS ecosystem. Replace the brittle regex-based correction harvester with an explicit intent-driven authoring engine and a dual-track data model.

---

## 1. Executive Summary & Goal

Where the previous correction harvester failed due to naive regex pattern matching that mistook ephemeral conversation for permanent rules, this implementation introduces a **Hermes-inspired Self-Learning Loop**. 

**The goal is to implement:**
1. **Explicit Intent & Structured Synthesis (`/learn`)**: A new `/learn` command that triggers an LLM-driven authoring workflow to generate procedural skills and declarative memories, instead of passive regex scraping.
2. **Dual-Track Knowledge Representation**:
   - **Declarative Memory** for facts, preferences, and constraints, stored in `MEMORY.md` and `USER.md` with strict character budgets.
   - **Procedural Skills** for workflows, indexed via ultra-short ($\le 60$-character) descriptions and loaded on-demand.
3. **Progressive Disclosure & Frozen Prompt Caching**: Injecting only frozen snapshots of declarative memories and lightweight skill indexes at session start.
4. **Self-Balancing Character Budgets**: A memory tool that enforces strict character limits, forcing LLM-driven compaction instead of endless appending.

---

## 2. Architecture & Data Model

### Dual-Track Data Model
- **Declarative Memory (`MEMORY.md` & `USER.md`)**:
  - **Location**: `~/.config/achios/MEMORY.md` (bot facts/constraints) and `~/.config/achios/USER.md` (Aki's profile/preferences).
  - **Format**: Entries are separated by the `\n§\n` delimiter.
  - **Constraint**: Hard 2,500-character budget per file.
- **Procedural Skills (`SKILL.md`)**:
  - **Location**: `~/.gemini/antigravity-cli/skills/<name>/SKILL.md`
  - **Format**: Executable runbooks with standardized sections (`Prerequisites`, `Procedure`, `Pitfalls`, `Verification`).
  - **Constraint**: Frontmatter descriptions must be $\le 60$ characters.

### 5 Core Invariants / Safeguards
1. **Explicit Validation**: No conversational text is permanently stored without an explicit tool invocation or `/learn` directive.
2. **Budget Enforcement**: Memory mutation operations must fail if they exceed the 2,500-character limit, forcing a `batch` consolidation operation instead.
3. **Prefix Cache Safety**: `USER.md` and `MEMORY.md` are loaded as frozen text blocks on session launch to ensure 100% LLM prefix cache hits.
4. **Graph Pruning & Frontmatter Discipline**: Skill definitions strictly enforce $\le 60$-character descriptions for the index routing.
5. **Truthfulness Fallback**: `evening_debrief.py` will only report rules that have explicitly been synthesized and committed.

---

## 3. Detailed Task-by-Task Implementation

### Task 1: Declarative Memory Storage & Mutation Engine
**Files:**
- Create: `/home/achibukz/Code/GitHub/achiAgy/src/memory_engine.py`

- [x] Implement `MemoryEngine` class to manage `~/.config/achios/MEMORY.md` and `~/.config/achios/USER.md`.
- [x] Support operations: `add(text: str)`, `replace(old: str, new: str)`, `remove(text: str)`, and `batch(mutations: list[dict])`.
- [x] Implement the `\n§\n` delimiter logic for parsing and stringifying memories.
- [x] Enforce the 2,500-character budget per file, raising an error if an `add` or `replace` exceeds the limit, returning instructions to use `batch` for consolidation.
- [x] Create `init_storage()` to ensure files and directories exist.

**Verification command:**
```bash
/home/achibukz/.local/share/achios/venv/bin/python -c "from src.memory_engine import MemoryEngine; m=MemoryEngine(); m.init_storage()"
ls -la ~/.config/achios/*.md
```

---

### Task 2: Integrate `manage_memory` Tool & Frozen System Prompt Caching in `achiAgy`
**Files:**
- Modify: `/home/achibukz/Code/GitHub/achiAgy/src/bot.py`
- Modify: `/home/achibukz/Code/GitHub/achiAgy/src/session_manager.py` (if needed for context)

- [x] Import `MemoryEngine` in `bot.py` or the agent tool registry.
- [x] Define the `manage_memory` tool schema (actions: `add`, `replace`, `remove`, `batch`) and wire it to the `MemoryEngine`.
- [x] Update the system prompt initialization to read `USER.md` and `MEMORY.md` directly from disk on session start and inject them as frozen text blocks at the very top of the prompt.
- [x] Inject the lightweight skill index (skill names and $\le 60$-char descriptions from `~/.gemini/antigravity-cli/skills/`) into the prompt.

**Verification command:**
```bash
grep -n "manage_memory" /home/achibukz/Code/GitHub/achiAgy/src/bot.py
```

---

### Task 3: Implement `/learn` Command with Hermes-style Strict Authoring Prompt in `achiAgy`
**Files:**
- Modify: `/home/achibukz/Code/GitHub/achiAgy/src/bot.py`

- [x] Add `cmd_learn(update, context)` handler for `/learn <topic>`.
- [x] Construct a strict Hermes-style authoring prompt for the LLM when `/learn` is invoked.
  - The prompt must instruct the agent to use `manage_memory` for declarative facts.
  - For procedural workflows, instruct it to write a new `SKILL.md` to `~/.gemini/antigravity-cli/skills/<name>/SKILL.md`.
  - Enforce the $\le 60$-character description constraint for skills.
  - Require the agent to sanitize input (e.g. dropping weird invisible unicode characters).
- [x] Route the `/learn` execution pipeline identically to how `cmd_tasks` works, passing the strict prompt.

**Verification command:**
```bash
grep -n "cmd_learn" /home/achibukz/Code/GitHub/achiAgy/src/bot.py
```

---

### Task 4: Upgrade `AIS-OS` Scripts
**Files:**
- Modify: `/home/achibukz/Code/GitHub/AIS-OS/scripts/extract_corrections.py`
- Modify: `/home/achibukz/Code/GitHub/AIS-OS/scripts/vault_inbox_sync.py`
- Modify: `/home/achibukz/Code/GitHub/AIS-OS/scripts/evening_debrief.py`

- [x] **`extract_corrections.py`**: Rip out the brittle regex logic entirely. Replace it with an LLM gating call (using `gy` CLI or direct Gemini API) to classify and extract true permanent corrections from the `tgdb` logs into structured memory updates via `manage_memory` or new skills.
- [x] **`vault_inbox_sync.py`**: Ensure it commits updates to `.agentrules` (if still used as a backup) or the new `MEMORY.md` paths if they fall under a synced vault. Since memory is now in `~/.config/achios/`, update sync logic if memory should be synced to `achiMem`.
- [x] **`evening_debrief.py`**: Fix the truthfulness logic. Update `get_corrections_today()` to scan the new `MEMORY.md` history or a structured log of explicit `manage_memory` operations, rather than scraping arbitrary `tgdb` files, to prevent hallucinating unapplied rules.

**Verification command:**
```bash
/home/achibukz/.local/share/achios/venv/bin/python /home/achibukz/Code/GitHub/AIS-OS/scripts/extract_corrections.py --dry-run
```

---

### Task 5: Unit Tests Suite
**Files:**
- Create: `tests/test_memory_engine.py` (in `achiAgy`)
- Create: `tests/test_learn_command.py` (in `achiAgy`)
- Modify: `tests/test_extract_corrections.py` (in `AIS-OS`)

- [x] Write `test_memory_engine.py` to assert the 2,500-char budget limit raises an exception, the `\n§\n` delimiter works, and atomic replacements succeed.
- [x] Write `test_learn_command.py` to mock the `/learn` execution and verify the strict prompt is constructed correctly.
- [x] Update `test_extract_corrections.py` to mock the LLM gating behavior and verify false positives (like "Take note of this Google One subscription cancellation") are ignored.

**Verification command:**
```bash
/home/achibukz/.local/share/achios/venv/bin/python -m pytest /home/achibukz/Code/GitHub/achiAgy/tests/test_memory_engine.py
```

---

### Task 6: End-to-End Verification Runbook & Telegram Smoke Test
- [x] Start the updated `achiAgy` daemon.
- [x] In Telegram, test the Declarative Memory via `/learn My favorite coffee is black`. Verify `~/.config/achios/USER.md` contains the new fact surrounded by `\n§\n`.
- [x] Test the Procedural Skill via `/learn how to deploy the static site`. Verify a new folder is created in `~/.gemini/antigravity-cli/skills/` with a `SKILL.md` that has a $\le 60$-character description.
- [x] Force a budget overflow: Write a 2,600-character block using the `manage_memory` tool and verify the tool rejects the addition and demands a `batch` consolidation.
- [x] Verify `evening_debrief.py --dry-run` accurately reflects only the successfully applied rules.
