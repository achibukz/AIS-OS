# PStack Skills Catalog & Architecture Showcase

A comprehensive audit of the 45 skills and agentic principles from [`cursor/plugins/pstack/skills`](https://github.com/cursor/plugins/tree/main/pstack/skills). This guide outlines the most valuable tools for our achiOS and Asa workflows, the structural patterns behind them, and key takeaways to improve our agent prompts, orchestrators, and knowledge systems.

---

## 1. Executive Summary & Top Recommendations

The `pstack` skills library is built around three core pillars:
1. **Autonomous Orchestration & Learning:** Structured loops to fan out workers (`swarm`, `arena`), reconstruct session context (`recall`), record audit trails (`show-me-your-work`), and self-tune skills from transcripts (`reflect`).
2. **Cognitive & Investigative Tools:** Deep exploration separating runtime mechanics (`how`), historical motivation (`why`), impact analysis (`blast-radius`), and unstructured debugging (`figure-it-out`).
3. **Composable Engineering Principles (`principle-*`):** 20 atomic behavioral invariants that teach models how to reason, prune context, sequence changes, and enforce safety structurally.

---

## 2. High-Impact Workflow Skills

### A. Autonomous Orchestration & Reflection

| Skill | Purpose | Value for achiOS / Asa |
|---|---|---|
| **`reflect`** | Spawns 3 parallel review subagents (Judgment, Tooling, Divergent) over active JSONL transcripts to extract durable lessons and route them into skill edits or backlog tickets. | Bridges our self-learning loop (`memory_engine.py`) with skill evolution. Automatically detects prompt edge cases and tunes `SKILL.md` files. |
| **`show-me-your-work`** | Maintains a lightweight, append-only TSV decision log (`ts`, `phase`, `decision`, `why`, `evidence`, `result`) verified against transcripts and audited by a secondary cross-model subagent. | Provides machine-readable, verifiable audit trails for long-running autonomous runs in Asa and achiOS background services. |
| **`recall`** | Mines recent chat history and shared external records (git, PRs, issues, error traces) to synthesize a 5-bullet state capsule before starting or resuming work. | Eliminates context amnesia across multi-session tasks. Gives subagents immediate awareness of where prior work left off. |
| **`swarm`** | Fans out $N$ parallel workers, tracks them through discrete phases, drains outputs, and synthesizes a single structured deliverable. | Direct reference design for Asa's multi-agent research and code generation pipelines. |
| **`arena`** | Solves ambiguous architectural tasks by running head-to-head model competitions (e.g. Claude Opus vs. Gemini Flash) with blind voting to select the optimal design. | Excellent for evaluating competing implementation patterns before committing to large refactors. |

---

### B. Investigation, QA & Risk Analysis

| Skill | Purpose | Value for achiOS / Asa |
|---|---|---|
| **`blast-radius`** | Performs deep pre-change impact analysis. Identifies "the one fact it is safe because of", checks cross-module boundaries, and proves safety via scripts before merge. | Enhances QA workflows. Replaces vague risk lists with concrete, verifiable invariant checks. |
| **`why`** | Discovers and queries multiple evidence streams (git history, PR discussions, ADRs, issue comments) in parallel to uncover why code was written a certain way. | Answers architectural motivation questions without hallucinating intent. Perfect companion for codebase exploration. |
| **`how`** | Traces exact runtime behavior, call stacks, and data flows through direct code analysis. | Isolates runtime mechanisms from historical motivation (`how` for runtime, `why` for intent). |
| **`figure-it-out`** | Autonomous investigative loop for hard bugs lacking obvious stack traces or clear error messages. | Guides agents through systematic hypothesis testing without thrashing or getting stuck in loops. |

---

### C. Writing, Documentation & Communication

| Skill | Purpose | Value for achiOS / Asa |
|---|---|---|
| **`unslop`** *(Installed)* | Strips AI tells, puffery, fake "is", robotic tags, and conversational filler. | Enforces our constitutional anti-slop invariant across all agents, notes, and briefings. |
| **`technical-writing`** | Enforces a 4-layer technical writing standard: Diátaxis document modes (Tutorial, How-to, Reference, Explanation), Google developer style directness, Simplified Technical English (STE) sentence boundaries, and Global English clarity. | Standardizes documentation across achiMem, schoolMem, and repository READMEs so docs are readable on the first pass. |
| **`no-comments`** | Audits and strips redundant, self-evident, or stale comments, retaining only non-obvious invariants and architectural rationale. | Keeps codebases clean and minimizes cognitive noise during agent context loading. |

---

## 3. Composable Engineering Principles (`principle-*`)

`pstack` packages 20 standalone principle skills that can be referenced or adopted into agent system prompts:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PSTACK PRINCIPLE SUITE                             │
├──────────────────────────┬──────────────────────────────────────────────┤
│ Context & Efficiency     │ principle-guard-the-context-window           │
│                          │ principle-laziness-protocol                  │
│                          │ principle-subtract-before-you-add            │
├──────────────────────────┼──────────────────────────────────────────────┤
│ Verification & Execution │ principle-prove-it-works                     │
│                          │ principle-sequence-verifiable-units          │
│                          │ principle-outcome-oriented-execution         │
├──────────────────────────┼──────────────────────────────────────────────┤
│ Architecture & Design    │ principle-boundary-discipline                │
│                          │ principle-exhaust-the-design-space           │
│                          │ principle-foundational-thinking              │
│                          │ principle-redesign-from-first-principles     │
│                          │ principle-model-the-domain                   │
├──────────────────────────┼──────────────────────────────────────────────┤
│ Structural Safety        │ principle-encode-lessons-in-structure        │
│                          │ principle-type-system-discipline             │
│                          │ principle-make-operations-idempotent         │
│                          │ principle-separate-before-serializing-shared │
│                          │ principle-migrate-callers-then-delete-apis   │
│                          │ principle-fix-root-causes                    │
├──────────────────────────┼──────────────────────────────────────────────┤
│ Ergonomics & Autonomy    │ principle-experience-first                   │
│                          │ principle-never-block-on-the-human           │
│                          │ principle-minimize-reader-load               │
│                          │ principle-build-the-lever                    │
└──────────────────────────┴──────────────────────────────────────────────┘
```

### Key Principles Explained:

1. **`principle-encode-lessons-in-structure`**: Never rely on memory or prose warnings to prevent repeated bugs. Encode lessons into lints, type constraints, automated tests, or directory layouts so the system enforces correctness mechanically.
2. **`principle-guard-the-context-window`**: Treat the context window as a scarce resource. Use progressive disclosure, pointers, and subagent delegation rather than dumping massive raw logs or full files into the primary chat.
3. **`principle-sequence-verifiable-units`**: Break complex features into small, atomic units where each step leaves the system in a green, verified state before proceeding to the next.
4. **`principle-subtract-before-you-add`**: Remove dead code, redundant branches, and unused helpers before adding new features. Building on top of a simpler baseline reduces overall complexity.
5. **`principle-prove-it-works`**: Never declare a task complete based on assumption. Produce concrete, reproducible proof (test output, diff check, curl response).

---

## 4. Key Lessons to Level Up Our Workflow

### 1. Transcript-Driven Skill Refinement (`reflect` pattern)
Instead of manually tweaking prompt rules when an agent makes a mistake, we can run a structured analysis over the agent transcript. By examining where tool calls failed or required user correction, we can automatically update skill descriptions and constraints.

### 2. TSV Decision Logs for Autonomous Tasks (`show-me-your-work` pattern)
When running unattended background jobs or multi-step research in Asa, logging decisions to a clean TSV file provides a standardized audit trail. This makes it effortless to review agent choices in a tabular format without sifting through thousands of log lines.

### 3. Separation of Runtime (`how`) vs. Historical Intent (`why`)
When exploring complex unfamiliar systems, separating mechanical code tracing from historical intent discovery prevents confusion. Use `how` for call graphs and state flows, and `why` for git commits, PR discussions, and ADRs.

### 4. Four-Layer Documentation Standard (`technical-writing` pattern)
Combining `unslop` with the 4-layer documentation standard elevates our wiki notes in `achiMem` and `schoolMem`:
* **Diátaxis Framing:** Strictly separate tutorials, how-to guides, reference tables, and conceptual explanations.
* **Google Developer Style:** Active voice, present tense, direct commands, conditions before actions.
* **Simplified Technical English:** One clear instruction per sentence, under 25 words.
* **Global English:** Unambiguous pronouns and modifiers with zero slang or idioms.

---

## 5. Complete Index of 45 PStack Skills

```
• architect                                  • principle-experience-first
• arena                                      • principle-fix-root-causes
• automate-me                                • principle-foundational-thinking
• blast-radius                               • principle-guard-the-context-window
• bro                                        • principle-laziness-protocol
• create-verification-skill                  • principle-make-operations-idempotent
• figure-it-out                              • principle-migrate-callers-then-delete-legacy-apis
• grokbot                                    • principle-minimize-reader-load
• how                                        • principle-model-the-domain
• interrogate                                • principle-never-block-on-the-human
• maintain-verification-skill                • principle-outcome-oriented-execution
• no-comments                                • principle-prove-it-works
• poteto-mode                                • principle-redesign-from-first-principles
• principle-boundary-discipline              • principle-separate-before-serializing-shared-state
• principle-build-the-lever                  • principle-sequence-verifiable-units
• principle-encode-lessons-in-structure      • principle-subtract-before-you-add
• principle-exhaust-the-design-space         • principle-type-system-discipline
• recall                                     • teach
• reflect                                    • technical-writing
• setup-pstack                               • typescript-best-practices
• show-me-your-work                          • unslop
• swarm                                      • why
• tdd
```
