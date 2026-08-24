# Matt Pocock Workflow Suite Integration & Wayfinder-asa Hybrid Architecture Audit

**Author:** Agi (achiOS Core / Antigravity Pair)  
**Date:** August 25, 2026 (PHT)  
**Target Repository:** achiOS (`~/Code/GitHub/AIS-OS/`)  
**Status:** Ready for Claude Code Review & Audit  

---

## 1. Executive Summary

Matt Pocock released an updated catalog of 37 agentic skills and workflows (`https://github.com/mattpocock/skills`) centered around structured planning, deep-module architecture, tree-based alignment interviews, and multi-session navigation (`wayfinder`).

This document captures the taxonomy of these workflows, details the mechanics of `wayfinder` and `grilling`, and outlines an architectural bridge to connect **Wayfinder** with **`asa` (achiOS Subagent Dispatch)** so that resource-heavy research steps run out-of-band on Gemini 3.7 Flash, preserving Claude Code rate limits and 5-hour rolling token windows.

---

## 2. Taxonomy of Matt Pocock's Skills Suite

The repository organizes workflows into four primary domains:

### A. Planning, Alignment & Roadmapping
1. **`grilling` / `grill-me`**: Tree-based alignment protocol. Models decisions as a directed graph ("design tree") and works through the unblocked "frontier" of questions in structured rounds (`❓ Q1`, `❓ Q2`) with concrete recommendations.
2. **`grill-with-docs`**: Runs the grilling interview while producing durable architecture documentation (ADRs, context files) in real-time.
3. **`wayfinder`**: Navigates massive, multi-session initiatives by maintaining a single Master Map issue and resolving small, dependency-linked decision tickets one session at a time.
4. **`to-spec`**: Compiles conversation context and agreed decisions into a formal engineering specification.
5. **`to-tickets`**: Decomposes plans and specifications into vertical-slice tracer-bullet tickets.
6. **`to-questionnaire`**: Converts unresolvable decision branches into structured questionnaires for human stakeholders.

### B. Architecture & Codebase Design
1. **`codebase-design`**: Vocabulary and patterns based on John Ousterhout’s *Philosophy of Software Design* (deep modules, narrow interfaces, information hiding).
2. **`domain-modeling`**: Clarifies and locks ubiquitous language and glossary definitions for a project.
3. **`improve-codebase-architecture`**: Scans repos for shallow modules and visualizes deepening opportunities via HTML reports.
4. **`setup-ts-deep-modules`**: Sets up `dependency-cruiser` in TypeScript codebases to enforce strict module boundaries.
5. **`migrate-to-shoehorn`**: Refactors TypeScript tests away from unsafe `as` type casting to `@total-typescript/shoehorn`.

### C. Execution, Triage & Tooling
1. **`ask-matt`**: Meta-router skill that examines the current workspace state and suggests which skill to trigger.
2. **`diagnosing-bugs`**: Systematic scientific debugging loop based on explicit hypotheses and evidence collection.
3. **`tdd`**: Red-Green-Refactor test-driven development loop.
4. **`implement`**: Ticket execution engine adhering strictly to predefined specifications.
5. **`triage`**: Moves issues and PRs through a state machine of triage roles.
6. **`wizard`**: Generates interactive bash scripts for manual/credential setup that cannot be automated.
7. **`resolving-merge-conflicts`**: Step-by-step git merge conflict resolution protocol.

### D. Meta & Ergonomics
1. **`wait-what`**: Halts the assistant when an explanation fails to land and forces a clear re-pitch.
2. **`writing-for-agents`**: Best practices and standards for drafting concise, trigger-accurate agent skills.
3. **`teach`**: Explains complex technical topics interactively within the local workspace.
4. **`claude-handoff`**: Compacts session state and passes context to a fresh background agent.

---

## 3. Deep Dive: `grilling` & `grill-me` Evolution

### Legacy `grill-me` vs New `grilling`
- **Legacy:** Asked loose questions one-by-one in conversation, often stalling or drifting off-topic.
- **New Architecture:**
  - **Design Tree:** Maps decisions and their prerequisite branches.
  - **Frontier Rounds:** Identifies all decisions that can be answered *now* without guessing future answers, asking them together with recommended choices.
  - **Autonomous Fact Finding:** When a question depends on environment/code facts, the agent dispatches a background lookup instead of burdening the user.
  - **Frontier Empty = Done:** The session concludes only when all branches are visited and nothing is silently assumed.

---

## 4. Deep Dive: Wayfinder Architecture ("Plan, Don't Do")

Wayfinder prevents agents from getting lost in large projects by decoupling planning from execution.

```
+-------------------------------------------------------------------+
|                        THE MASTER MAP                             |
|                        (wayfinder:map)                            |
|                                                                   |
|  * Destination: Clear 1-2 sentence target                         |
|  * Decisions So Far: Index of closed ticket summaries             |
|  * Not Yet Specified: Fog of war (future in-scope ideas)          |
|  * Out of Scope: Explicitly excluded work                         |
+---------------------------------+---------------------------------+
                                  |
               +------------------+------------------+
               |                                     |
    [Frontier Ticket #1]                  [Frontier Ticket #2]
       (Research - AFK)                    (Grilling - HITL)
               |                                     |
               v                                     v
       Unblocks Ticket #3                     Unblocks Ticket #4
       (Prototype - HITL)                      (Task - AFK/HITL)
```

### The 4 Ticket Types
1. **Research (AFK):** Fact-gathering from docs, APIs, or codebase. Resolved by background agent.
2. **Grilling (HITL):** Alignment conversation resolving an architectural or product branch.
3. **Prototype (HITL):** Quick throwaway stub/UI to validate assumptions.
4. **Task (HITL/AFK):** Prerequisite setup action (e.g. provisioning keys, schema staging).

### Invariant: One Ticket Per Session
Each session loads the map, claims **one** unblocked frontier ticket, resolves it, records the decision, updates the map, graduates items from the fog of war, and closes the ticket.

---

## 5. The achiOS Bridge: Wayfinder + `asa` (Token-Optimization)

### The Problem in Claude Code
When Claude Code runs Wayfinder's Step 5 (*"Fire the research subagents"*), running native Claude subagents consumes substantial token allowance and hits Claude's 5-hour rolling rate limits rapidly.

### The Solution: Delegating Research to `asa`
By customizing `research/SKILL.md`, Claude Code can offload research tickets directly to `asa` running on **Gemini 3.7 Flash High** (STORM multi-agent mode) at near-zero cost.

```
[Claude Code - Wayfinder Session]
           |
           | 1. Claims research ticket
           | 2. Executes background bash call:
           v
  $ asa run --agent ari --name <ticket-slug> "<research question & context>"
           |
           +---------------------------------------------+
           | (Out-of-band execution on Achibuntu server) |
           |  - Muses fan-out research                   |
           |  - Primary source doc retrieval             |
           |  - Althea fact-check audit                  |
           +---------------------------------------------+
           |
           | 3. Claude collects:
           v
  $ asa wait <ticket-slug> --format md
           |
           | 4. Saves findings to markdown & updates Wayfinder Map
           v
[Ticket Resolved & Closed]
```

### Proposed `research/SKILL.md` Hook
```markdown
---
name: research
description: Investigate a question against high-trust primary sources using asa background workers.
---

Spin up an autonomous background research worker via `asa` to preserve Claude token context:

1. Dispatch the background worker:
   `asa run --name <ticket-slug> "<question with clear scope and primary source targets>"`

2. Block and retrieve the markdown findings:
   `asa wait <ticket-slug> --format md`

3. Write findings to `docs/research/<ticket-slug>.md`, append summary to the Wayfinder map, and close the ticket.
```

---

## 6. Claude Code Audit Checklist

When reviewing this integration with Claude Code, verify the following points:

- [ ] **Skill Isolation:** Verify that `skillshare` synced the 37 skills cleanly without conflicting with custom achiOS skills (`asa`, `sync-achimem`, `sessionclaude`).
- [ ] **`research/SKILL.md` Customization:** Confirm that replacing generic subagent spawning with `asa run` adheres to Claude Code non-interactive background bash execution.
- [ ] **Issue Tracker Backend:** Decide whether to use GitHub Issues or local markdown files (`docs/wayfinder/`) as the backing store for Wayfinder maps in achiOS.
- [ ] **Alias Coexistence:** Ensure `/grill-me` cleanly aliases to `/grilling` in both Claude and Antigravity.
- [ ] **Token Efficiency Benchmark:** Validate token savings by running a sample research ticket through `asa` vs native Claude Code subagent.
