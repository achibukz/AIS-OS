# achiOS Self-Learning Loop & Hermes Knowledge-Base Architecture Findings

**Date:** August 20, 2026  
**Author:** Antigravity AI Engine (Google DeepMind)  
**Context:** Pair programming session with Aki (`achibukz`) covering the complete implementation of the Hermes-style Self-Learning Loop and analysis of Obsidian `achiMem` knowledge base interactions.

---

## 1. Executive Summary

We have fully implemented, verified, and unit-tested the **Hermes-style Self-Learning Loop** across `achiAgy` (Telegram AI Bot) and `AIS-OS` (Autonomous Agent Harness). In addition, we extracted Aki's complete profile and preferences from the `achiMem` Obsidian vault to initialize `~/.config/achios/USER.md`, and analyzed Hermes Agent's repository (`~/.hermes/hermes-agent`) for Obsidian / knowledge-base patterns.

---

## 2. Completed Self-Learning Loop Implementation

### A. Declarative Memory Engine (`achiAgy/src/memory_engine.py`)
* **Storage Locations:** `~/.config/achios/MEMORY.md` (system/agent facts) and `~/.config/achios/USER.md` (user profile/preferences).
* **Section Delimiter:** Raw entries are separated by `\n§\n` section signs.
* **Operations:** Atomic `add`, `replace`, `remove`, and `batch` mutations.
* **Budget Constraint:** Strict 2,500-character ceiling per store. When an addition would exceed 2,500 characters, it raises `MemoryBudgetError`, prompting the model to use `batch` consolidation.
* **Concurrency:** POSIX file locking (`fcntl`) with process-level re-entrant lock tracking to prevent deadlocks across nested calls.
* **CLI Interface:** `python -m src.memory_engine init|add|replace|remove|batch|list`.

### B. `manage_memory` & Frozen Prefix Caching (`achiAgy/src/bot.py`)
* **Prefix-Safe Prompt Caching:** `build_frozen_system_prompt()` reads `USER.md` and `MEMORY.md` and prepends them as frozen text blocks **only on initial conversation turn** (`if session.conversation_id is None`). Subsequent turns reuse the cached conversation session (`--conversation <id>`), maintaining 100% LLM prefix cache hits and minimizing latency/costs.
* **Dynamic Skill Index:** `build_skill_index()` scans `~/.gemini/antigravity-cli/skills/` and `builtin/skills/`, enforcing a hard $\le 60$-character description constraint for lightweight routing.

### C. Explicit `/learn` Command (`achiAgy/src/bot.py`)
* **Authoring Routing:** Evaluates user requests and routes to either:
  * **Declarative Memory** (via `manage_memory`) for facts, personal preferences, and operational constraints.
  * **Procedural Skills** (via `~/.gemini/antigravity-cli/skills/<name>/SKILL.md`) for executable workflows, tool scripts, and procedures.
* **Quality Guards:** Enforces frontmatter constraints ($\le 60$ char description), Antigravity tool naming conventions (`run_command`, `view_file`, `replace_file_content`), and Unicode sanitization.
* **Access:** Available via Telegram `/learn <topic>` command, autocomplete menu, and `./learn` shortcut.

### D. AIS-OS Harvesting Scripts Upgrade
* **`extract_corrections.py`:** Replaced brittle regex matching with candidate trigger pre-filtering and structured memory commits. Ephemeral remarks, receipt notes, and subscription cancellations (e.g. Google One) are suppressed; true permanent preferences are committed to `MemoryEngine`, `.agentrules`, and `decisions/log.md`.
* **`evening_debrief.py`:** Updated `get_corrections_today()` to only report verified, explicitly committed rules from `decisions/log.md` and `.agentrules`, guaranteeing zero hallucinated debrief rules.
* **`vault_inbox_sync.py`:** Integrated with the upgraded extraction pipeline.

### E. Test Suite Verification
* **`achiAgy` Test Suite:** 25/25 unit tests passing (`test_memory_engine.py`, `test_learn_command.py`, `test_bot_routing.py`, `test_session_metrics.py`, `test_tui_and_streaming.py`).
* **`AIS-OS` Test Suite:** 10/10 self-learning tests passing (`test_extract_corrections.py`, `test_evening_debrief.py`).

---

## 3. Populated `USER.md` Profile (from `achiMem`)

Extracted from `achiMem/wiki/personal/` (`_profile.md`, `voice.md`, `education.md`, `work-history.md`, `fitness.md`, `banking-setup.md`) and written to `~/.config/achios/USER.md` (1,666 / 2,500 characters, 66.6% utilization):

```markdown
Identity: Abram Aki R. Bukuhan (goes by Aki). Location: Manila, Philippines (PHT, UTC+8). 3rd year BS Computer Science (Software Technology) student at De La Salle University (DLSU) Manila, graduating August 2027. AVP for Human Resource Development at La Salle Computer Society (LSCS).
§
Technical Background: QA Engineer, Data Analyst, and Full-Stack Developer. Deep QA expertise (110+ automated tests at 90%+ coverage, Puppeteer suites, self-built CI/CD gates). Languages & Tools: Python, TypeScript/JavaScript, Java, Swift, Go, SQL, Docker, Linux, Neovim.
§
Communication Style: Open with hedges ("Honestly," "I would say," "So"), state concrete numbers/facts, and candidly own limitations/gaps without bluffing. Taglish for reasoning, English for conclusions. Prefers concise, direct phrasing ("all good", "we" when problem-solving together).
§
Emoji Palette & Tone Guardrails: Allowed warm/self-deprecating emojis: 🥰 😭 🙂‍↕️ 🫡 😍 🫶 💙 💖. BANNED: Corporate/hustle emojis (🚀, 💪, 📈, 🔥, 🎯). Never use corporate jargon or buzzwords like "amenable", "leverage", "synergy", or "holistic".
§
Operating Environment: Primary dev environments are macOS and headless Linux server (Achibuntu). achiOS agentic OS is hosted at ~/Code/GitHub/AIS-OS/ and telegram bot at ~/Code/GitHub/achiAgy/. Primary knowledge base is Obsidian vault achiMem (~/Documents/Obsidian/achiMem/).
§
Financial & Banking: GoTyme is primary checking/transacting, Tonik for high-yield savings/stashes, and GCash for daily utilities.
§
Health & Routines: Progressive overload strength training (3–5 sessions/week, PPL or Upper/Lower split), high-protein nutrition, and prioritizing 7–8 hours quality sleep.
```

---

## 4. Hermes Knowledge-Base & Obsidian Interaction Analysis

Research conducted in `~/.hermes/hermes-agent` revealed two core architectural paradigms:

### 1. Filesystem-First Obsidian Skill (`skills/note-taking/obsidian/SKILL.md`)
* **No UI/Electron Automation:** Hermes explicitly warns against automating Obsidian via GUI / accessibility trees due to massive node tree overhead.
* **Native Tool Primitives:** Interacts with vaults directly over the filesystem using `read_file`, `write_file`, `patch`, and `search_files` resolved against `OBSIDIAN_VAULT_PATH` (`~/Documents/Obsidian/achiMem`).
* **Wikilinks & Anchored Updates:** Generates standard `[[Wikilinks]]` and uses anchored patches (replacing known header blocks) for atomic section edits.

### 2. Karpathy LLM-Wiki & `book-to-skill` Pattern (`virgiliojr94/book-to-skill`)
* **Three-Layer Compounding Vault:**
  * **Layer 1 (`raw/`):** Immutable source material (articles, session notes, PDFs).
  * **Layer 2 (`wiki/`):** Compiled entity pages (`entities/`, `concepts/`, `personal/`) synthesized once and kept current.
  * **Layer 3 (`SCHEMA.md`, `index.md`, `log.md`):** Conventions, content catalog, and append-only activity tracking.
* **On-Demand Lazy Loading (`references/`):** Rather than creating monolithic 1,000-line skill files, Hermes uses a lean `<200`-line `SKILL.md` overview that references deep topic files inside a `references/` subdirectory (e.g. `skills/<name>/references/<topic>.md`), loaded only when required.

---

## 5. How achiOS Currently Interacts with `achiMem`

* **Session Lifecycle Hooks:** In `AIS-OS/.claude/settings.json`, `SessionEnd` hooks call `scripts/achimem_capture.py` to write session stubs into `achiMem/raw/sessions/` and enrich them via tool-less LLM calls. `SessionStart` recalls recent sessions.
* **Memory Separation:**
  * `achiOS` (`~/Code/GitHub/AIS-OS/`): Holds **doing** (tasks, orchestration, agents, build decisions).
  * `achiMem` (`~/Documents/Obsidian/achiMem/`): Holds **knowing** (long-term personal wiki, conceptual syntheses, immutable session archives).

---

## 6. Recommended 2-Tier Architecture for achiOS + achiMem

```
                     ┌──────────────────────────────────────────────┐
                     │           Aki (Telegram / CLI)               │
                     └──────────────────────┬───────────────────────┘
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
    ┌───────────────────────────┐                             ┌───────────────────────────┐
    │          TIER 1           │                             │          TIER 2           │
    │    Fast Working Memory    │                             │  Deep Compounding Vault   │
    ├───────────────────────────┤                             ├───────────────────────────┤
    │ ~/.config/achios/USER.md  │                             │ ~/Documents/Obsidian/     │
    │ ~/.config/achios/MEMORY.md│                             │   achiMem/wiki/           │
    │                           │                             │   achiMem/raw/            │
    │ • Hard 2.5k char budget   │                             │   achiMem/log.md          │
    │ • Frozen in prompt prefix │                             │                           │
    │ • Zero cache-bust latency │                             │ • Full entities & concepts│
    │ • Instant Telegram access │                             │ • Lazy-loaded on demand   │
    └──────────────┬────────────┘                             └─────────────▲─────────────┘
                   │                                                        │
                   │ (periodic harvest / consolidation via sync daemon)     │
                   └────────────────────────────────────────────────────────┘
```

1. **Keep Tier 1 Lean:** Maintain `USER.md` and `MEMORY.md` strictly under 2,500 characters for high-speed, cost-effective prompt prefix caching.
2. **Use the `references/` Pattern for Skills:** When distilling complex topics via `/learn`, generate a clean `SKILL.md` and place extended reference documentation inside `~/.gemini/antigravity-cli/skills/<name>/references/`.
3. **Compound into `achiMem`:** Continue archiving transcripts in `achiMem/raw/sessions/` and use `vault_inbox_sync.py` to periodically promote consolidated `/learn` topics into `achiMem/wiki/`.
