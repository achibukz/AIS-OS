# Dynamic CLI Skill Synthesizer — Implementation Plan for achiOS

## 1. Context & Objectives

As part of achiOS continuous self-improvement, the **Dynamic CLI Skill Synthesizer** bridges the gap between ad-hoc conversational workflows and reusable, automated CLI tools. 

Instead of relying on fragile, multi-step agent bash commands or heavy MCP servers, achiOS adopts the **Hermes "Footprint Ladder"** principle:
> *Whenever an agent or human performs a repeatable multi-step workflow, synthesize a clean, deterministic Python CLI script under `scripts/` accompanied by a lightweight `SKILL.md` playbook.*

This design ensures:
1. **Zero Prompt Drift & Hallucination:** Logic runs through audited, deterministic Python code.
2. **Universal Compatibility (`agentskills.io`):** Skills are discovered and executed identically across **Claude Code**, **Antigravity (Gemini)**, and **Hermes**.
3. **Safety First:** Mandatory `--dry-run` and `--help` flags on every generated tool.

---

## 2. Research & Comparison Baseline

### A. Hermes Agent (Nous Research) Paradigm
* **Footprint Ladder:** Prefers code extension → CLI command + skill → service tool → plugin → MCP.
* **Progressive Disclosure:** 
  * Level 0: Metadata index in system prompt (~3k tokens max).
  * Level 1: Core `SKILL.md` overview & execution rules.
  * Level 2: On-demand `references/` or `scripts/`.
* **Autonomous Distillation:** Background review fork (`_iters_since_skill >= 10` or `/learn`) captures multi-step terminal patterns into `~/.hermes/skills/`.
* **Curator:** Automated inactivity pruning (30d stale, 90d archive) and consolidation with `.curator_backups/` snapshots.

### B. Anthropic `skill-creator` (`anthropics/skills`) Paradigm
* **Eval-Driven Engineering:** Rigorous test sets, trigger accuracy evaluations, and variance analysis.
* **Trigger Optimization:** Optimizes frontmatter `description` to prevent false-positive/false-negative triggers.
* **Visual Review:** HTML-based viewer (`eval_viewer/generate_review.py`) for inspecting metrics.

---

## 3. achiOS Architectural Blueprint

```text
                               ┌─────────────────────────────┐
                               │  Dialogue / Workflow Trace  │
                               │  (or explicit user request) │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │ scripts/synthesize_skill.py │
                               └──────────────┬──────────────┘
                                              │
                ┌─────────────────────────────┼─────────────────────────────┐
                ▼                             ▼                             ▼
   ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
   │    1. Python CLI Tool     │ │   2. Universal Playbook   │ │    3. Pytest Test Case    │
   │    `scripts/<name>.py`    │ │ `.claude/skills/<name>/`  │ │ `tests/test_<name>.py`    │
   │ • argparse, --help        │ │ • SKILL.md (agentskills)  │ │ • Unit tests for logic    │
   │ • mandatory --dry-run     │ │ • Concise triggers        │ │ • CLI arg parsing tests   │
   │ • JSON output mode        │ │ • references/ (L2 docs)   │ │                           │
   └───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

---

## 4. Detailed Component Specifications

### 4.1. The Generator: `scripts/synthesize_skill.py`
A CLI utility that accepts parameters or extracts context from recent session logs to scaffold new skills.

* **CLI Syntax:**
  ```bash
  python scripts/synthesize_skill.py \
      --name "vault_backup" \
      --description "Backs up achiMem and schoolMem to local storage and remote HDD" \
      --template "cli-tool" \
      --args "destination:str,force:bool"
  ```
* **Template Choices:**
  * `cli-tool`: General-purpose deterministic task.
  * `vault-extractor`: Reads/transforms notes across Obsidian vaults (`achiMem`/`schoolMem`).
  * `telegram-notifier`: Formats state digests and sends via `scripts/telegram_notify.py`.
  * `google-service`: Authenticates with Google Workspace via existing `~/.config/achios/google_token*.json`.

### 4.2. Synthesized Python Script Standard (`scripts/<name>.py`)
Every synthesized tool must adhere to strict structural constraints:
* **Imports:** Uses shared achiOS modules where applicable (`from telegram_notify import send`).
* **Environment:** Compatible with the uv virtualenv (`~/.local/share/achios/venv/bin/python`).
* **Flags Required:**
  * `--dry-run`: Prints simulated actions and JSON payload without mutating filesystem or external services.
  * `--json`: Outputs raw JSON to `stdout` for programmatic consumption by agents.
  * `--verbose` / `-v`: Optional detailed logging.
* **Exit Codes:** Clean `0` on success, non-zero on failure with descriptive error to `stderr`.

### 4.3. Universal Playbook (`.claude/skills/<name>/SKILL.md`)
Conforms to the `agentskills.io` standard:
```markdown
---
name: <name>
description: <Trigger description <= 100 characters>
---

# <name>

<Overview of the workflow and purpose.>

## How to Execute

```bash
# Dry run simulation:
~/.local/share/achios/venv/bin/python scripts/<name>.py [args] --dry-run

# Live execution:
~/.local/share/achios/venv/bin/python scripts/<name>.py [args]
```

## Invariants & Rules
- Do NOT rewrite or run raw bash snippets for this workflow; use the Python script.
- Always inspect output before chaining subsequent actions.
```

### 4.4. The achiOS Curator (`scripts/curator.py`)
* Maintains `data/skill_usage.json` recording invocation counts and last-used timestamps.
* Scans skills periodically:
  * Moves unused one-off skills (>60 days inactive) to `archives/skills/<name>/`.
  * Creates timestamped `tar.gz` backups under `.curator_backups/` before any archival operation.

---

## 5. Integration with Existing achiOS Subsystems

1. **Autonomous Correction Harvester (`scripts/extract_corrections.py`):**
   * When `extract_corrections.py` processes `tgdb/` transcripts, multi-step bash sequences can be detected and recommended in the evening debrief as `[skill candidates]`.
2. **Daily / Evening Debriefs (`scripts/evening_debrief.py`):**
   * Summarizes newly synthesized skills and flags stale skills scheduled for archiving.
3. **Decisions Log (`decisions/log.md`):**
   * Automatically logs architectural decisions when new skills are minted.

---

## 6. Phased Implementation Roadmap

* **Phase 1: Core Synthesizer & Templates**
  * Implement `scripts/synthesize_skill.py`.
  * Build template skeletons (`cli-tool`, `vault-extractor`, `telegram-task`).
  * Add unit tests in `tests/test_synthesize_skill.py`.
* **Phase 2: Validation & Execution Harness**
  * Auto-run `--help` and `pytest` on generated tools during creation.
  * Register skill creation playbook in `.claude/skills/synthesize-skill/SKILL.md`.
* **Phase 3: Curator & Telemetry**
  * Implement `scripts/curator.py` for usage tracking and archival.
  * Connect telemetry hooks into bot wrappers (`telegram-bot.sh`).
