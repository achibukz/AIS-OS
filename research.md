# 🔬 Asa Research Backlog & Inquiry Register

> **Purpose:** A dedicated register for deep research topics, investigative inquiries, and epistemic deep dives for **Asa** (the STORM / muses research pipeline) to investigate and synthesize into research dossiers.
> 
> Kept separate from [tasks.md](file:///home/achibukz/Code/GitHub/AIS-OS/tasks.md) so engineering and operational tasks remain strictly actionable without getting bloated by long-term research questions.

---

## 🤖 AI Engineering & Agent Systems

### 1. SOTA Multi-Perspective Epistemic Research Architectures (STORM & Beyond)
- **Research Question:** How do frontier deep research systems (Stanford STORM, Exa Research, Perplexity Deep Research) structure recursive perspective-generating question matrices, citation-grounding trees, and multi-agent dialectic synthesis?
- **Inquiry Lenses:**
  - *Query Expansion:* Algorithmic generation of orthogonal expert viewpoints to eliminate confirmation bias.
  - *Verification Matrices:* Deterministic fact-checking layers (e.g. Alethea audit) against raw retrieval sources before final synthesis.
  - *Context Optimization:* Minimizing token waste while retaining full academic and technical citations.
- **Asa Worker Presets:** `muses` (parallel gatherers) → `alethea` (fact-checker) → `athena` (synthesizer)
- **Deliverable:** Technical architecture breakdown and integration guide for Asa's `workflows/research.md`.

### 2. Autonomous Agent Memory Models & Curation Strategies
- **Research Question:** What are the most effective architectures for long-term agent memory across turn-based sessions (Hermes episodic memory, MemGPT/Letta hierarchical tiers, and Markdown-backed vaults like Obsidian)?
- **Inquiry Lenses:**
  - *Pruning & Eviction:* Mathematical decay functions vs semantic relevance filtering under hard token/character budgets (e.g. 2,500 chars).
  - *Autonomous Mutation:* Heuristics for determining when an agent should append, replace, or delete memory entries without user intervention.
  - *Provenance Tracking:* Verifying statement provenance (`[stated]`, `[observed]`, `[inferred]`) to prevent hallucinatory memory drift.
- **Deliverable:** Comparative research paper on memory architectures for local/headless personal agent OSs.

### 3. Prompt Injection Defense for Unattended Bypass-Permission Agents
- **Research Question:** What defense-in-depth patterns effectively neutralize indirect prompt injection in autonomous messaging-driven agents (Telegram/Discord) operating with bypassed tool permissions?
- **Inquiry Lenses:**
  - *Input Sanitization:* Pre-execution taint analysis for pasted URLs, emails, and forwarded user content.
  - *Privilege Separation:* Subprocess isolation, read-only filesystem guards, and non-root execution environments.
  - *Dual-LLM Architecture:* Fast air-gapped auditor models screening inbound payloads before passing to the primary tool-using agent.
- **Deliverable:** Security threat model and defensive implementation playbook for `achiOS` and `achiAGY`.

---

## 🎓 Academic & Thesis (Software Technology)

### 4. Multimodal Vision-Language Architectures for Short-Form Video Engagement
- **Research Question:** What are the current state-of-the-art vision-language models and temporal sampling techniques for predicting multimodal user engagement (virality, completion rates, watch time) in short-form video content (TikTok, Reels, Shorts)?
- **Inquiry Lenses:**
  - *Model Architectures:* Benchmarking VideoLLaMA2, Qwen2.5-VL, and Video-ChatGPT on fine-grained visual-audio-textual alignment.
  - *Feature Extraction:* Sparse uniform frame sampling vs optical flow and scene-boundary keyframe extraction.
  - *Multimodal Fusion:* Cross-attention vs early concatenation for temporal video embeddings, audio transcripts, and metadata.
- **Deliverable:** Literature review and baseline experimental matrix for Software Technology thesis.

### 5. Distributed Consensus & Fault Tolerance in Edge/Constrained Node Clusters
- **Research Question:** How do modern lightweight consensus algorithms (Raft variants, SQLite WAL replication via LiteFS/rqlite) perform on heterogeneous, intermittent edge networks (e.g. local Mac + headless home server over Tailscale)?
- **Inquiry Lenses:**
  - *Network Partitions:* Handling high-latency or intermittent connectivity without split-brain state corruption.
  - *Resource Overhead:* Memory and CPU footprints of consensus protocols on low-power consumer hardware (Intel Skylake / ARM).
- **Deliverable:** Architectural primer and study notes for STDISCM (Distributed Systems).

---

## 💼 Career, Tax & Regulatory Intelligence

### 6. Philippine Tax & Labor Framework for Voluntary Corporate Internships
- **Research Question:** What are the exact tax obligations, statutory exemptions, and labor standards governing monthly allowances (e.g. ₱15,000/mo) for voluntary, non-academic corporate student internships in the Philippines?
- **Inquiry Lenses:**
  - *Tax Status:* Applicability of withholding tax on compensation vs non-taxable allowance under the TRAIN Law / NIRC, and whether companies issue BIR Form 2316 or 2307.
  - *Statutory Coverage:* SSS, PhilHealth, and Pag-IBIG applicability for voluntary interns vs standard employees under DOLE DO 149-16 and CHED CMO 104 guidelines.
  - *Corporate Offboarding:* Portability of corporate HMO benefits and transition traps when entering full-time roles.
- **Deliverable:** Practical tax and statutory compliance guide for tech interns in Philippine multinational hubs.

---

## 💳 Financial Engineering & Digital Banking

### 7. High-Yield Digital Banking Optimization & Interest Stacking in the Philippines
- **Research Question:** What is the optimal mathematical and liquidity distribution model across high-yield Philippine digital banks (Maya, Tonik, GoTyme, SeaBank) taking into account tiered interest caps, spend missions, and deposit insurance limits?
- **Inquiry Lenses:**
  - *Yield Optimization:* Calculating net effective APY after 20% final withholding tax on Maya (10–15% missions on ₱100k) vs Tonik Stashes (6%) vs SeaBank (4.5%).
  - *Risk & Insurance:* Maintaining total principal exposure within the ₱500,000 PDIC maximum per banking institution.
  - *Frictionless Routing:* Free clearinghouse hubs (e.g. GoTyme free InstaPay transfers) for zero-fee capital rotation.
- **Deliverable:** Quantitative allocation strategy and monthly capital rotation cheat sheet.

### 8. NFC Mobile Payments & Apple Pay Rollout in the Philippine Banking Ecosystem
- **Research Question:** What is the current regulatory landscape (BSP QR Ph mandates, NFC tokenization standards) and timeline for Apple Pay / Google Wallet merchant adoption among major Philippine banks (BPI, BDO, Maya)?
- **Inquiry Lenses:**
  - *Infrastructure Readiness:* POS terminal EMV contactless adoption rates across Metro Manila retail merchants.
  - *Interchange & Fee Structure:* How Apple's fee model impacts local card issuers and what regulatory milestones remain.
- **Deliverable:** Market intelligence brief on the trajectory of contactless mobile payments in the Philippines.
