# Optimizing CI/CD, Automated Testing, and PR Verification for Subagent Swarms Across GitHub Repositories

> **Delivered:** 2026-08-30 (PHT, UTC+8)  
> **Author / Engine:** Asa Research Pipeline (Gemini 3.1 Pro High · 5-Lens STORM + Athena Synthesis + Althea Audit)  
> **Topic Reference:** [research.md#11-optimizing-cicd-automated-testing-and-pr-verification-for-subagent-swarms-across-github-repositories](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md#11-optimizing-cicd-automated-testing-and-pr-verification-for-subagent-swarms-across-github-repositories) · [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md)

---

## Executive Summary

Autonomous coding subagents (Aea, Aya, Asta, Luna) introduce structural challenges to traditional CI/CD pipelines. Treating probabilistic subagents as human developers breaks deterministic pipelines through flaky test loops, token depletion, hallucinated mock passes, and prompt injection vulnerabilities in PR bodies.

To scale agentic engineering across multi-repo ecosystems (`AIS-OS`, `achiCore`, `schoolMem`, `career-ops`), the CI/CD pipeline must decouple orchestration from execution:
1. **Local Persistent Orchestration & Worktrees:** Subagent sessions run inside isolated `.worktrees/subagent-id` directories managed by local daemons on Achibuntu. This eliminates GitHub Actions per-minute idle billing during LLM thinking loops.
2. **Context Precision via AST Slicing:** Rather than dumping full test suites into agent context windows, test files are sliced via AST dependencies to preserve token budgets and maximize prefix caching.
3. **Execution Sandboxing in Remote CI:** Because git worktrees provide filesystem isolation but not environment or network isolation, untrusted subagent code execution and integration tests run inside ephemeral, unprivileged GitHub Actions runners (or Docker/gVisor containers).
4. **Deterministic Feedback Self-Correction Loops:** Test failures in CI are captured and fed directly back into agent context windows, forcing automated self-correction before human review.
5. **Zero-Trust Review & HITL Verification:** High-reasoning reviewer agents (Luna/Opus) perform security and correctness audits on diffs, requiring explicit Human-in-the-Loop (HITL) reproduction runs before merging.

---

## 5-Lens Research Synthesis

### Lens 1: Practitioner & Fast Feedback Gating (`cicd-practitioner`)
- **Git Worktree Primitive:** Standard branch switching clobbers local context windows and uncommitted files. Orchestrators must dispatch agents into isolated `.worktrees/subagent-id` paths that share `.git` history but maintain distinct working trees.
- **Environment Isolation Gap:** Worktrees isolate files on disk but do not isolate listening ports, database connections, or running daemons. Concurrent subagents require dynamic port assignment or ephemeral container instances.
- **TDD Red-to-Green Proof Gates:** Subagents must be evaluated with strict proof gates (`--gate`): tests must fail before implementation and pass after implementation. Passing gates prove the patch works; pre-existing passing tests prove nothing.

### Lens 2: Multi-Repo Architecture & Dependency Layout (`cicd-architect`)
- **Containerization for Blast-Radius Containment:** Because subagents execute generated shell commands, CI harnesses must execute code in isolated container namespaces to protect the host machine from unconstrained file modifications.
- **Immutable Artifact Passing:** Sharing patches, execution logs, and AST caches between coder agents (Aea) and reviewer agents (Luna) utilizes immutable artifact pipelines (`actions/upload-artifact@v4` / `actions/download-artifact@v4`).
- **Sibling Repository Resolution:** GitHub Actions resolves sibling repositories side-by-side using `actions/checkout@v4` with explicit `path:` arguments. However, dynamic branch resolution requires a centralized manifest to prevent version drift between `AIS-OS` and `achiCore`.
- **Versioned Test Fixtures:** Polyrepo test contracts require shared schemas and fixtures to be distributed as versioned packages or Testcontainer images rather than brittle static files.

### Lens 3: Security, Failure Analysis & Skepticism (`cicd-skeptic`)
- **Confused Deputy & Prompt Injection Vulnerabilities:** Public GitHub issues and PR descriptions can contain indirect prompt injections (categorized as "GitLost" and "PromptPwnd"). Agents triggered via `issue_comment` or `pull_request_target` risk executing arbitrary commands or exfiltrating `GITHUB_TOKEN`.
- **Default Read-Only Permissions:** Workflows running subagents must enforce strict minimal GitHub Actions permissions (`permissions: contents: read`) to prevent unauthorized commits or secret exfiltration.
- **Token Depletion in Flaky Test Loops:** When subagents encounter non-deterministic test failures, they enter circular repair loops, burning hundreds of thousands of tokens without fixing root causes. Flaky tests must be automatically quarantined.
- **Structured Tool Validation:** API-level JSON schemas (Anthropic tool use, OpenAI structured outputs) neutralize open-ended shell injection payloads before commands reach the runner.

### Lens 4: Token Economics & Compute Tiering (`cicd-economist`)
- **Model Cascading:** Routing high-volume "sense-reason-act" loops and preliminary test gates to fast, high-throughput models (Gemini 3.7 Flash) while reserving heavy reasoning models (Claude 3.7 Sonnet / Opus 4.6) for complex reviews and failure resolution cuts LLM costs by 2.5x to 3x.
- **Test Suite Slicing:** Supplying targeted test methods and direct imports rather than entire test suites prevents "lost-in-the-middle" attention degradation and mechanically caps prompt token size.
- **AST Metadata & Prefix Caching:** Generating stable AST context chunks enables provider-level prefix caching, dropping recurring prompt costs by up to 90% when context remains identical across turns.
- **Local Runner Economics:** Persistent local runner orchestration (Achibuntu) eliminates idle cloud compute minute charges while subagents wait on LLM API streaming responses.

### Lens 5: Evolution & Prior Art (`cicd-historian`)
- **Evolution of Agent Boundaries:** In 2023, early PR bots (Sweep, AutoPR) pushed reactive, unverified code to human reviewers. In 2024–2026, systems evolved toward isolated pre-PR execution sandboxes (SWE-bench Docker environments, Devin cloud VMs) that test patches against fail-to-pass suites before surfacing PRs.
- **GitHub Agentic Infrastructure:** GitHub Agentic Workflows (`gh-aw`) compile natural language automation objectives into hardened GitHub Actions `lock.yml` files running inside read-only gVisor/Docker sandboxes with mandatory HITL approval.
- **Deterministic CI as Feedback:** Deterministic linters, typecheckers, and test runners operate as conversational feedback loops: when a gate fails, error diagnostics are returned directly to the agent context for self-repair.

---

## Fact-Check Audit Verdicts (Althea)

| Metric | Count |
|---|---|
| **Total Claims Audited** | 33 |
| **Supported** | 11 |
| **Partial** | 0 |
| **Unsupported** | 20 (primarily uncited synthesis/recommendation statements) |
| **Contradicted** | 2 (over-claiming worktree isolation; container scaling limits) |
| **Unverifiable** | 0 |
| **FABRICATED SOURCES** | **0** |

### Key Fact-Check Adjustments:
1. **Worktree Isolation Boundaries:** Git worktrees provide strictly filesystem separation; they do *not* provide runtime environment, port, or network isolation.
2. **Container Scaling Constraints:** While containers isolate blast radius, research from SWE-bench benchmarks demonstrates that heavy Docker environments frequently introduce disk exhaustion and build flakiness at scale.

---

## Architectural Recommendations for achiOS

1. **Multi-Tiered Verification Pipeline:**
   - *Tier 0 (Pre-Commit / Local Worktree):* Fast (<5s) AST syntax checks, link verifiers, and targeted unit test slices.
   - *Tier 1 (Pre-PR Local Proof Gate):* Local pytest run in ephemeral `asa` worktree against red-to-green proof criteria.
   - *Tier 2 (Remote GitHub Actions CI):* Isolated matrix builds (Python 3.11, 3.12, 3.13) with read-only token scopes.
   - *Tier 3 (Zero-Trust Review & HITL):* Automated Luna code audit followed by human manual reproduction steps.

2. **Automated Flaky Test Quarantine:**
   - Introduce pytest flaky test detection with maximum retry bounds (e.g. 2 attempts) to prevent subagents from burning tokens on non-deterministic infrastructure failures.

3. **Secure Agent Dispatch Protocol:**
   - Disallow direct PR merging or unrestricted shell execution from webhook triggers. Require maintainer-approved label dispatch (`@achibukz`) and isolate subagents into read-only runner environments.
