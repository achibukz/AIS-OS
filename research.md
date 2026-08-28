# 🔬 Asa Research Backlog & Inquiry Register

> **Purpose:** A dedicated register for deep research topics, investigative inquiries, and epistemic deep dives for **Asa** (the STORM / muses research pipeline) to investigate and synthesize into research dossiers.
> 
> **Dual-Entry Protocol:** Every research inquiry is paired with an actionable tracking item in [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md). In `research.md`, inquiries are elaborated with the bounded research question, 3–4 orthogonal inquiry lenses (perspectives/angles), and target deliverables (`achiMem/raw/` markdown notes and/or PDF reports).

---

## 🤖 AI Engineering & Agent Systems

### 1. SOTA Multi-Perspective Epistemic Research Architectures (STORM & Beyond)
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!med`)
- **Research Question:** How do frontier deep research systems (Stanford STORM, Exa Research, Perplexity Deep Research) structure recursive perspective-generating question matrices, citation-grounding trees, and multi-agent dialectic synthesis?
- **Inquiry Lenses:**
  - *Query Expansion:* Algorithmic generation of orthogonal expert viewpoints to eliminate confirmation bias.
  - *Verification Matrices:* Deterministic fact-checking layers (e.g. Alethea audit) against raw retrieval sources before final synthesis.
  - *Context Optimization:* Minimizing token waste while retaining full academic and technical citations.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-sota-epistemic-research-architectures.md`

### 2. Autonomous Agent Memory Models & Curation Strategies
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!med`)
- **Research Question:** What are the most effective architectures for long-term agent memory across turn-based sessions (Hermes episodic memory, MemGPT/Letta hierarchical tiers, and Markdown-backed vaults like Obsidian)?
- **Inquiry Lenses:**
  - *Pruning & Eviction:* Mathematical decay functions vs semantic relevance filtering under hard token/character budgets (e.g. 2,500 chars).
  - *Autonomous Mutation:* Heuristics for determining when an agent should append, replace, or delete memory entries without user intervention.
  - *Provenance Tracking:* Verifying statement provenance (`[stated]`, `[observed]`, `[inferred]`) to prevent hallucinatory memory drift.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-autonomous-agent-memory-models.md`

### 3. Prompt Injection Defense for Unattended Bypass-Permission Agents
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What defense-in-depth patterns effectively neutralize indirect prompt injection in autonomous messaging-driven agents (Telegram/Discord) operating with bypassed tool permissions?
- **Inquiry Lenses:**
  - *Input Sanitization:* Pre-execution taint analysis for pasted URLs, emails, and forwarded user content.
  - *Privilege Separation:* Subprocess isolation, read-only filesystem guards, and non-root execution environments.
  - *Dual-LLM Architecture:* Fast air-gapped auditor models screening inbound payloads before passing to the primary tool-using agent.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-prompt-injection-defense-playbook.md`

---

## 🛠️ Infrastructure, Tooling & Dev Environment

### 4. Continuous Bi-Directional File Synchronization Across Achibuntu and macOS (Syncthing vs Alternatives)
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!med`)
- **Research Question:** What is the optimal, low-friction continuous file synchronization architecture (Syncthing, Mutagen, Unison, or rsync/lsyncd daemon) between headless Linux (Achibuntu) and macOS (MacBook Air) to eliminate repetitive manual git fetch/pull cycles without introducing git index corruption or file-watch battery drain?
- **Inquiry Lenses:**
  - *Sync Protocols & Topology:* Peer-to-peer daemon vs background daemon over Tailscale; evaluating network transport overhead and NAT traversal.
  - *Git Safety & File Locking:* Handling `.git/` directory conflicts, untracked lockfiles, index state synchronization, and `.stignore` / ignore rule strategies to prevent repo corruption.
  - *macOS Ergonomics & Resource Impact:* Background battery/CPU efficiency of file-watching daemons on Apple Silicon vs on-demand sync triggers.
  - *Conflict Resolution & Edge Cases:* Automated conflict resolution policies when edits occur offline or simultaneously on both machines.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-25-syncthing-achibuntu-macos-sync-evaluation.md`

---

## 🎓 Academic & Thesis (Software Technology)

### 5. Multimodal Vision-Language Architectures for Short-Form Video Engagement
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What are the current state-of-the-art vision-language models and temporal sampling techniques for predicting multimodal user engagement (virality, completion rates, watch time) in short-form video content (TikTok, Reels, Shorts)?
- **Inquiry Lenses:**
  - *Model Architectures:* Benchmarking VideoLLaMA2, Qwen2.5-VL, and Video-ChatGPT on fine-grained visual-audio-textual alignment.
  - *Feature Extraction:* Sparse uniform frame sampling vs optical flow and scene-boundary keyframe extraction.
  - *Multimodal Fusion:* Cross-attention vs early concatenation for temporal video embeddings, audio transcripts, and metadata.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-multimodal-short-form-video-engagement.md`

---

## 💼 Career, Tax & Regulatory Intelligence

---

## 💳 Financial Engineering & Digital Banking

### 6. High-Yield Digital Banking Optimization & Interest Stacking in the Philippines
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What is the optimal mathematical and liquidity distribution model across high-yield Philippine digital banks (Maya, Tonik, GoTyme, SeaBank) taking into account tiered interest caps, spend missions, and deposit insurance limits?
- **Inquiry Lenses:**
  - *Yield Optimization:* Calculating net effective APY after 20% final withholding tax on Maya (10–15% missions on ₱100k) vs Tonik Stashes (6%) vs SeaBank (4.5%).
  - *Risk & Insurance:* Maintaining total principal exposure within the ₱500,000 PDIC maximum per banking institution.
  - *Frictionless Routing:* Free clearinghouse hubs (e.g. GoTyme free InstaPay transfers) for zero-fee capital rotation.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-ph-high-yield-digital-banking-optimization.md`

---

## 🥗 Health, Nutrition & Fitness Technology

### 7. AI-Integrated Food and Calorie Tracking Apps Landscape
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What is the comprehensive competitive landscape of AI-integrated calorie and macro tracking applications (multimodal photo, voice, and text logging), contrasting subscription apps (e.g. Amy by AloaLabs, Cal AI, MacroFactor, MyFitnessPal) against free, freemium, open-source, and one-time payment alternatives across features, estimation accuracy, pricing, and user sentiment?
- **Inquiry Lenses:**
  - *Subscription Landscape:* Tiered pricing, premium AI features, and user lock-in of major subscription apps (Amy by AloaLabs, Cal AI, Foodvisor, MyFitnessPal, MacroFactor).
  - *Free, Freemium & One-Time Payment Models:* Viable alternatives offering lifetime licenses, generous free tiers, BYO-API-key setups, or open-source local models (Foodnoms, Cronometer, SnapCalorie, OpenNutriTracker, CalorieSY).
  - *Technical Mechanics & Accuracy Pitfalls:* Multimodal computer vision architectures, volume/depth estimation errors (hidden oils, sauce, mixed meal segmentation) vs lab-verified food databases.
  - *User Sentiment & Dark Patterns:* Real-world community reviews from Reddit/App Store regarding aggressive trial billing, hallucinated macro counts, and adherence friction.
  - *Ecosystem & Privacy:* HealthKit/Health Connect integration, on-device vs cloud image processing, and adaptive expenditure algorithms.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-25-ai-food-calorie-tracking-apps-landscape.md` and `~/Documents/Obsidian/achiMem/raw/2026-08-25-ai-food-calorie-tracking-apps-landscape.pdf`

### 8. Using Google Antigravity as Model Backend for Hermes Agent (Plugins, Proxies & Bridge Repos)
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** Can Google Antigravity (AGY / antigravity-cli / Gemini & Claude proxy/backends) be used as the model provider for NousResearch Hermes Agent (`~/.hermes/hermes-agent`), and what plugins, custom provider profiles, reverse proxies, or open-source GitHub repositories bridge this connection if no official integration exists?
- **Inquiry Lenses:**
  - *Hermes Model Provider Architecture:* How Hermes loads and routes models via `ProviderProfile` plugins, custom `base_url`s, OpenAI-compatible chat completion protocols, and tool calling schemas.
  - *Antigravity Backend & Authentication:* How Antigravity exposes models (Gemini 3.7 Flash/Pro, Claude 3.7 Sonnet/Opus), auth token lifecycle, internal Google Cloud Code endpoints, and headless CLI invocations.
  - *Bridge Proxies & Community Repositories:* GitHub repositories, LiteLLM adapters, reverse proxies, and bridge daemons translating OpenAI API requests to Antigravity / Gemini protocols.
  - *Technical Viability & Incompatibilities:* Function calling / tool use format translation, streaming SSE handling, rate limits, latency, and operational stability.
  - *Implementation Blueprint & Meta-Workflow:* Step-by-step custom plugin setup (`$HERMES_HOME/plugins/model-providers/antigravity/`), proxy daemon setup, or alternative CLI delegation workflows in achiOS.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-25-antigravity-models-in-hermes-agent-feasibility.md`

### 9. Whisper Flow / Wispr Flow Free and Open-Source Alternatives Deep Dive
- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What are the most capable free and open-source alternatives to Whisper Flow / Wispr Flow for system-wide AI voice typing and dictation across macOS, Linux, and Windows, detailing features, feature gaps (filler removal, context-aware rewriting, auto-formatting), local model inference engines (whisper.cpp, faster-whisper), and complete installation playbooks?
- **Inquiry Lenses:**
  - *Ecosystem Survey:* Free desktop apps (Superwhisper free, MacWhisper free, Buzz, Aqua Voice, Voice In, Willow Voice) and their core capabilities.
  - *Pure Open-Source Local Stacks:* Self-hosted/local Whisper implementations (whisper.cpp, faster-whisper, WhisperWriter, nerd-dictation, whisper-auto-type) with global hotkey cursor injection.
  - *Feature Parity & Gap Analysis:* Comparison against Wispr Flow (automatic filler removal, LLM post-processing, personal vocabulary, application-aware context, multi-language support, latency).
  - *Installation & Configuration Playbooks:* Concrete setup instructions, dependencies, permissions, and hotkey binding across macOS (Apple Silicon) and Linux/Windows.
  - *Tradeoffs & Benchmarks:* Offline privacy and hardware requirements (VRAM, CPU, RAM) vs cloud-based latency and free-tier limitations.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-28-whisper-flow-free-alternatives-deep-dive.md`

### 10. Integrating Codex into the achiOS Workflow — Multi-Agent Architecture, Model Hierarchy, and OS-Agnostic Engine Strategy

- **Task Reference:** [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** How should OpenAI Codex CLI be integrated into the achiOS multi-agent ecosystem — as a Hermes model backend (Hermes+Codex brain), as a direct model provider inside achiAgy replacing or supplementing `agy`, or as an MCP tool server — and what is the optimal model hierarchy, token economics, and task routing when stacking Codex, Claude Code, Gemini, and other engines together? This is additive, not a replacement — we are extending what we have.
- **Inquiry Lenses:**

  - *Lens 1 — Hermes + Codex Brain (Hermes as orchestrator, Codex as reasoning engine):*
    Evaluate running Hermes gateway with `provider: openai-codex` (OAuth, no per-token billing under subscription). Map what Hermes's tool harness (browser-use, Kanban DB, cron scheduling, 150+ skills, SQLite WAL sessions, 20+ messaging platform adapters) gains from o3/o4-mini or `codex-mini-latest` as the brain vs the current Nemotron-free baseline. Identify the specific task classes where this is strictly better than the current achiAgy+Gemini setup (e.g. long-horizon code planning, architecture review, autonomous SRE cron tasks). Document the pairing friction: auth flow, `hermes auth add openai-codex` OAuth steps, config.yaml changes, and what the `achiHermes` Hub topic would look like in the Telegram supergroup.

  - *Lens 2 — Codex as a Direct Model Provider in achiAgy (OS-agnostic engine layer):*
    Research what it takes to add Codex as a selectable model in `achiAgy/src/config.py` — either via `codex exec` subprocess wrapping (mirroring how `agy` is wrapped today) or via `codex mcp-server` (stdio MCP mount, cleaner tool-schema interface). Evaluate session continuity (`codex exec resume --last`), streaming NDJSON compatibility with `AgyClient`, and sandboxed code execution. Compare per-request latency and context limits (Codex: 200K ctx vs Gemini: 1M ctx). Answer whether Codex as an MCP-mounted engine inside achiAgy is the cleanest path toward OS-agnostic model routing (any model — Claude, Gemini, Codex, local — selectable per topic with zero code duplication).

  - *Lens 3 — Pros and Cons: Codex vs Claude Code as Orchestrators (Token Economics + Billing):*
    Direct comparison of using Codex CLI vs Claude Code as the primary agentic engine for achiOS. Dimensions: token billing model (Codex subscription seat vs Claude Code Max subscription vs per-token API), effective cost per complex coding task, context window constraints and their real-world impact on long tasks, tool quality (terminal, git, file ops, search), model ceiling (o3/o4-mini/Codex-1 vs Claude Opus 4.6 vs Gemini 3.1 Pro), and rate limits per plan tier. Include token consumption benchmarks if available from community reports.

  - *Lens 4 — Full Model Access Matrix and Task Routing Hierarchy:*
    Build a comprehensive matrix of every model accessible via Claude Code, Codex CLI, and Gemini/agy across all available tiers (free, subscription, API). Columns: context window, max output, reasoning quality tier, coding benchmark scores (SWE-Bench, HumanEval), tool-use reliability, multimodal capability, cost, and latency. From this matrix, define a recommended routing hierarchy for achiOS topics:
    - Which model handles everyday Telegram chat and task tracking (#General, daily brief)?
    - Which handles architectural review and long HITL sessions (#Aurora, #Ari)?
    - Which handles implementation tickets with heavy file mutations (#Aea)?
    - Which handles autonomous cron tasks and research pipelines (Asa, Atlas)?
    - Which handles emergencies and deep reasoning that rivals Opus (Sol, Luna, o3)?
    Include Sol, Luna, and other strong models (o3, o4-mini, Gemini 3.1 Pro High) in this comparison and identify which tasks they beat Opus at and which they don't.

  - *Lens 5 — Benefits of Adding Codex to the Stack (Additive Value, Not Replacement):*
    Document the concrete, non-overlapping value Codex CLI brings that Claude Code and agy do not cover today: native OpenAI subscription OAuth (no per-token billing for Codex-gated models), access to o3/o4-mini reasoning on demand, `codex exec review` as a dedicated code-review engine, Cloud task execution (`codex cloud`), sandbox isolation (`codex sandbox`), and `mcp-server` mode for composing Codex into any MCP-aware orchestrator. Frame this as an additive superpower layer on top of the existing achiOS stack, clarifying which new capabilities unlock without displacing Gemini Flash as the cheap everyday engine or Claude Opus as the heavy reasoning fallback.

  - *Lens 6 — OS-Agnostic Engine Rename and Architecture Implication:*
    Research how naming and structural changes to the `achiAgy` codebase (currently named after Google Antigravity) should be scoped to support a genuinely engine-agnostic architecture — where `agy`, `codex exec`, `claude -p`, or any future CLI agent can be swapped in per topic. What's the minimal rename surface (repo name, service names, config keys, systemd units, AGENTS.md, README) and what architectural changes in `AgyClient` make the engine truly pluggable? Document candidate names (e.g. `achiAgent`, `achiOS-agent`, `achihub`, `achicore`) and the trade-offs of each.

- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-28-codex-in-achios-workflow-and-model-hierarchy.md`
