# 🔬 Asa Research Backlog & Inquiry Register

> **Purpose:** A dedicated register for deep research topics, investigative inquiries, and epistemic deep dives for **Asa** (the STORM / muses research pipeline) to investigate and synthesize into research dossiers.
> 
> **Dual-Entry Protocol:** Every research inquiry is paired with an actionable tracking item in [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md). In `research.md`, inquiries are elaborated with the bounded research question, 3–4 orthogonal inquiry lenses (perspectives/angles), and target deliverables (`achiMem/raw/` markdown notes and/or PDF reports).

---

## 🤖 AI Engineering & Agent Systems

### 1. SOTA Multi-Perspective Epistemic Research Architectures (STORM & Beyond)
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!med`)
- **Research Question:** How do frontier deep research systems (Stanford STORM, Exa Research, Perplexity Deep Research) structure recursive perspective-generating question matrices, citation-grounding trees, and multi-agent dialectic synthesis?
- **Inquiry Lenses:**
  - *Query Expansion:* Algorithmic generation of orthogonal expert viewpoints to eliminate confirmation bias.
  - *Verification Matrices:* Deterministic fact-checking layers (e.g. Alethea audit) against raw retrieval sources before final synthesis.
  - *Context Optimization:* Minimizing token waste while retaining full academic and technical citations.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-sota-epistemic-research-architectures.md`

### 2. Autonomous Agent Memory Models & Curation Strategies
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!med`)
- **Research Question:** What are the most effective architectures for long-term agent memory across turn-based sessions (Hermes episodic memory, MemGPT/Letta hierarchical tiers, and Markdown-backed vaults like Obsidian)?
- **Inquiry Lenses:**
  - *Pruning & Eviction:* Mathematical decay functions vs semantic relevance filtering under hard token/character budgets (e.g. 2,500 chars).
  - *Autonomous Mutation:* Heuristics for determining when an agent should append, replace, or delete memory entries without user intervention.
  - *Provenance Tracking:* Verifying statement provenance (`[stated]`, `[observed]`, `[inferred]`) to prevent hallucinatory memory drift.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-autonomous-agent-memory-models.md`

### 3. Prompt Injection Defense for Unattended Bypass-Permission Agents
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What defense-in-depth patterns effectively neutralize indirect prompt injection in autonomous messaging-driven agents (Telegram/Discord) operating with bypassed tool permissions?
- **Inquiry Lenses:**
  - *Input Sanitization:* Pre-execution taint analysis for pasted URLs, emails, and forwarded user content.
  - *Privilege Separation:* Subprocess isolation, read-only filesystem guards, and non-root execution environments.
  - *Dual-LLM Architecture:* Fast air-gapped auditor models screening inbound payloads before passing to the primary tool-using agent.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-prompt-injection-defense-playbook.md`

---

## 🛠️ Infrastructure, Tooling & Dev Environment

### 4. Continuous Bi-Directional File Synchronization Across Achibuntu and macOS (Syncthing vs Alternatives)
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!med`)
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
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!high`)
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
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What is the optimal mathematical and liquidity distribution model across high-yield Philippine digital banks (Maya, Tonik, GoTyme, SeaBank) taking into account tiered interest caps, spend missions, and deposit insurance limits?
- **Inquiry Lenses:**
  - *Yield Optimization:* Calculating net effective APY after 20% final withholding tax on Maya (10–15% missions on ₱100k) vs Tonik Stashes (6%) vs SeaBank (4.5%).
  - *Risk & Insurance:* Maintaining total principal exposure within the ₱500,000 PDIC maximum per banking institution.
  - *Frictionless Routing:* Free clearinghouse hubs (e.g. GoTyme free InstaPay transfers) for zero-fee capital rotation.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-20-ph-high-yield-digital-banking-optimization.md`

---

## 🥗 Health, Nutrition & Fitness Technology

### 7. AI-Integrated Food and Calorie Tracking Apps Landscape
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** What is the comprehensive competitive landscape of AI-integrated calorie and macro tracking applications (multimodal photo, voice, and text logging), contrasting subscription apps (e.g. Amy by AloaLabs, Cal AI, MacroFactor, MyFitnessPal) against free, freemium, open-source, and one-time payment alternatives across features, estimation accuracy, pricing, and user sentiment?
- **Inquiry Lenses:**
  - *Subscription Landscape:* Tiered pricing, premium AI features, and user lock-in of major subscription apps (Amy by AloaLabs, Cal AI, Foodvisor, MyFitnessPal, MacroFactor).
  - *Free, Freemium & One-Time Payment Models:* Viable alternatives offering lifetime licenses, generous free tiers, BYO-API-key setups, or open-source local models (Foodnoms, Cronometer, SnapCalorie, OpenNutriTracker, CalorieSY).
  - *Technical Mechanics & Accuracy Pitfalls:* Multimodal computer vision architectures, volume/depth estimation errors (hidden oils, sauce, mixed meal segmentation) vs lab-verified food databases.
  - *User Sentiment & Dark Patterns:* Real-world community reviews from Reddit/App Store regarding aggressive trial billing, hallucinated macro counts, and adherence friction.
  - *Ecosystem & Privacy:* HealthKit/Health Connect integration, on-device vs cloud image processing, and adaptive expenditure algorithms.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-25-ai-food-calorie-tracking-apps-landscape.md` and `~/Documents/Obsidian/achiMem/raw/2026-08-25-ai-food-calorie-tracking-apps-landscape.pdf`

### 8. Using Google Antigravity as Model Backend for Hermes Agent (Plugins, Proxies & Bridge Repos)
- **Task Reference:** [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) (`!high`)
- **Research Question:** Can Google Antigravity (AGY / antigravity-cli / Gemini & Claude proxy/backends) be used as the model provider for NousResearch Hermes Agent (`~/.hermes/hermes-agent`), and what plugins, custom provider profiles, reverse proxies, or open-source GitHub repositories bridge this connection if no official integration exists?
- **Inquiry Lenses:**
  - *Hermes Model Provider Architecture:* How Hermes loads and routes models via `ProviderProfile` plugins, custom `base_url`s, OpenAI-compatible chat completion protocols, and tool calling schemas.
  - *Antigravity Backend & Authentication:* How Antigravity exposes models (Gemini 3.7 Flash/Pro, Claude 3.7 Sonnet/Opus), auth token lifecycle, internal Google Cloud Code endpoints, and headless CLI invocations.
  - *Bridge Proxies & Community Repositories:* GitHub repositories, LiteLLM adapters, reverse proxies, and bridge daemons translating OpenAI API requests to Antigravity / Gemini protocols.
  - *Technical Viability & Incompatibilities:* Function calling / tool use format translation, streaming SSE handling, rate limits, latency, and operational stability.
  - *Implementation Blueprint & Meta-Workflow:* Step-by-step custom plugin setup (`$HERMES_HOME/plugins/model-providers/antigravity/`), proxy daemon setup, or alternative CLI delegation workflows in achiOS.
- **Target Deliverable:** `~/Documents/Obsidian/achiMem/raw/2026-08-25-antigravity-models-in-hermes-agent-feasibility.md`

