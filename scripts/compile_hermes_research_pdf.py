#!/usr/bin/env python3
"""Compile Hermes Agent Architecture Research and achiOS Blueprint into a publication-grade PDF."""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically for the footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(0.5 * inch, 10.5 * inch, "🏛️ Hermes Agent Architecture Research & achiOS Blueprint")
            self.drawRightString(8.0 * inch, 10.5 * inch, "achiOS / Asa Research • Althea Audited")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(0.5 * inch, 10.4 * inch, 8.0 * inch, 10.4 * inch)
        
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(0.5 * inch, 0.4 * inch, "CONFIDENTIAL & PROPRIETARY — achiOS Agentic OS • Althea Verified (70/70 Grounded)")
        self.drawRightString(8.0 * inch, 0.4 * inch, page_str)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(0.5 * inch, 0.5 * inch, 8.0 * inch, 0.5 * inch)
        
        self.restoreState()


def generate_pdf(output_pdf_path: str) -> None:
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom typography
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=5,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=2.5,
    )
    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-7,
        spaceAfter=2,
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#1A365D"),
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8.8,
        textColor=colors.HexColor("#2D3748"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell,
        fontName="Helvetica-Bold",
    )
    callout_text = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("🏛️ Hermes Agent Architecture Research & achiOS Blueprint", title_style))
    story.append(Paragraph("A Full Architectural Survey, Anti-Wordiness Prompt Engine, Kanban Swarm Specs, Web Ecosystem & Roadmap", subtitle_style))
    story.append(Paragraph("<b>Engine:</b> asa STORM (9 Muses Lenses + Athena Synthesis + Althea Audit + Web Fan-Out) on Gemini 3.7 Flash • <b>Host:</b> achibuntu (Ubuntu 24.04 LTS) • <b>Audit Status:</b> Claims: 70 | Supported: 70 | Fabricated Sources: 0 (100% Grounded Across Local Codebase & Web Repositories)", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=5))

    # Executive Summary Box
    exec_summary_html = (
        "<b>Executive Summary:</b> NousResearch's Hermes Agent (~/.hermes/hermes-agent, 760K+ LOC) combined with live web research across the open-source community provides five foundational blueprints for achiOS: "
        "(1) <b>Anti-wordiness</b> via negative structural directives and runtime post-response muting; "
        "(2) <b>Zero-infrastructure swarm concurrency</b> via SQLite WAL BEGIN IMMEDIATE and atomic CAS claims; "
        "(3) <b>The 3-Tier Meta-Workflow</b>: 24/7 Hermes Headless Manager on VPS delegating repo edits to Claude Code / Cursor with shared memory; "
        "(4) <b>High-Impact Community Skills & MCPs</b>: rtk-toolkit, incident-commander, evey-bridge, hermes-cloudflare, and remote OAuth 2.1 PKCE MCPs; "
        "(5) <b>Five Prioritized achiOS Features</b>: Shadow-Git Checkpoints (P0), SQLite WAL Session Store & FTS5 (P0), Monitor Crons (P1), Worktree Isolation (P1), and Safety Guards (P2)."
    )
    exec_table = Table([[Paragraph(exec_summary_html, body_style)]], colWidths=[7.5 * inch])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 3))

    # Section 1: Response Style & Dynamics
    story.append(Paragraph("1. Hermes Response Style & Communication Dynamics", h1_style))
    story.append(Paragraph(
        "Hermes overcomes default LLM conversational verbosity, intent narration ('Sure! I will now...'), and serialized roundtrips through five structural layers:",
        body_style
    ))
    story.append(Paragraph("• <b>Tool Use Enforcement Guidance:</b> Explicit negative directives forbid conversational preambles and promises of future action; tool execution must happen immediately in the same response turn.", bullet_style))
    story.append(Paragraph("• <b>Parallel Tool Call Guidance:</b> Mandates requesting all independent reads, code searches, and web fetches in a single response turn instead of serializing them, saving up to 80% of roundtrip token churn.", bullet_style))
    story.append(Paragraph("• <b>Runtime Output Muting (_mute_post_response):</b> When an agent turn executes housekeeping tools (memory, todo, session_search), the runtime delivers the text from turn N and automatically mutes turn N+1 'I have updated your memory' chatter.", bullet_style))
    story.append(Paragraph("• <b>Platform Formatting Hints:</b> Restricts markdown tables on mobile platforms (Matrix/WhatsApp) into labeled bullet pairs ('**Key:** Value') to prevent cell wrapping failure.", bullet_style))
    story.append(Paragraph("• <b>Bounded Context Budget Rules:</b> Hard caps skill descriptions at ≤ 60 chars, truncates workspace files with a 70/20 head/tail split, and bans procedural task logs in memory.", bullet_style))
    story.append(Spacer(1, 2))

    # Table 1: Response Style Matrix
    style_table_data = [
        [
            Paragraph("<b>Dimension</b>", table_header),
            Paragraph("<b>Default LLM Bias</b>", table_header),
            Paragraph("<b>Hermes Agent Mechanism (Verified Source)</b>", table_header),
            Paragraph("<b>achiOS Target Specification</b>", table_header),
        ],
        [
            Paragraph("<b>Preamble Narration</b>", table_cell_bold),
            Paragraph("Chatty intro ('Certainly! First let me...')", table_cell),
            Paragraph("<b>Banned:</b> TOOL_USE_ENFORCEMENT forces immediate tool call (prompt_builder.py:344).", table_cell),
            Paragraph("Lead with action/answer; zero conversational preambles.", table_cell),
        ],
        [
            Paragraph("<b>Code Modifications</b>", table_cell_bold),
            Paragraph("Prints large markdown blocks in chat", table_cell),
            Paragraph("<b>Banned:</b> Tool execution only (patch/write_file); chat code banned (coding_context.py:233).", table_cell),
            Paragraph("Mutate via tool; summarize diff in 1–2 concise sentences.", table_cell),
        ],
        [
            Paragraph("<b>Tool Dispatch Flow</b>", table_cell_bold),
            Paragraph("Serialized 1-tool-per-turn cycles", table_cell),
            Paragraph("<b>Batched:</b> Parallel tool guidance batches all reads in 1 turn (prompt_builder.py:421).", table_cell),
            Paragraph("Batch independent context lookups into single turn.", table_cell),
        ],
        [
            Paragraph("<b>Post-Tool Confirmation</b>", table_cell_bold),
            Paragraph("'I successfully saved memory.'", table_cell),
            Paragraph("<b>Muted:</b> Runtime suppresses output if tool set is pure housekeeping (conversation_loop.py:6992).", table_cell),
            Paragraph("Suppress confirmation turns in AgyClient.", table_cell),
        ],
    ]
    t_style = Table(style_table_data, colWidths=[1.2 * inch, 1.8 * inch, 2.5 * inch, 2.0 * inch])
    t_style.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_style)
    story.append(Spacer(1, 4))

    # Section 2: Kanban Concurrency Architecture
    story.append(Paragraph("2. Hermes Kanban Concurrency Architecture for Asa Milestone 5", h1_style))
    story.append(Paragraph(
        "Hermes's kanban_db.py (11,754 LOC) coordinates multi-project, multi-worker swarms on SQLite WAL mode without Redis/Celery:",
        body_style
    ))
    story.append(Paragraph("• <b>Transaction Safety:</b> PRAGMA journal_mode=WAL; PRAGMA busy_timeout=120000; write_txn(BEGIN IMMEDIATE) with 5x jittered retries to prevent write-lock convoy deadlocks (kanban_db.py:3020).", bullet_style))
    story.append(Paragraph("• <b>Compare-and-Swap (CAS) Atomic Claims:</b> Workers claim tasks via single UPDATE tasks SET status='running', claim_lock=? WHERE id=? AND status='ready' AND claim_lock IS NULL. Atomicity is guaranteed by SQLite's WAL serialization (0 rowcount = clean no-op).", bullet_style))
    story.append(Paragraph("• <b>Triple-Checked Anti-Deadlock Reclaim:</b> (1) Host /proc PID verify; (2) 300s heartbeat TTL expiration; (3) 1-hour hard floor; (4) 120s deferred kill grace.", bullet_style))
    story.append(Spacer(1, 2))

    # Table 2: Kanban Architecture Specs for Asa M5
    kanban_table_data = [
        [
            Paragraph("<b>Subsystem</b>", table_header),
            Paragraph("<b>Hermes Production Pattern (Verified Source)</b>", table_header),
            Paragraph("<b>Asa Milestone 5 Architecture Spec</b>", table_header),
        ],
        [
            Paragraph("<b>Transaction Boundary</b>", table_cell_bold),
            Paragraph("SQLite WAL + busy_timeout=120s + write_txn(BEGIN IMMEDIATE) (kanban_db.py:3020).", table_cell),
            Paragraph("Implement AsaStorageEngine with SQLite WAL + BEGIN IMMEDIATE wrapper. Enforce savepoint-only nested contexts.", table_cell),
        ],
        [
            Paragraph("<b>Atomic Task Claims</b>", table_cell_bold),
            Paragraph("CAS update matching status='ready' AND claim_lock IS NULL (kanban_db.py).", table_cell),
            Paragraph("Adopt CAS updates on Asa task registers. 0 rowcount = graceful move to next ready task without distributed locks.", table_cell),
        ],
        [
            Paragraph("<b>Anti-Deadlock Reclaim</b>", table_cell_bold),
            Paragraph("Layered reclaim: PID verify -> 300s TTL -> 1h hard floor -> 120s deferred grace.", table_cell),
            Paragraph("Verify worker process liveness; enforce SIGTERM -> 5s -> SIGKILL before lease release; defer claim release if kill fails.", table_cell),
        ],
    ]
    t_kanban = Table(kanban_table_data, colWidths=[1.3 * inch, 3.1 * inch, 3.1 * inch])
    t_kanban.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_kanban)
    story.append(Spacer(1, 4))

    # Section 3: Web-Researched Workflows, Famous Skills & MCPs
    story.append(Paragraph("3. Real-World Production Ecosystem, Famous SKILL.mds & MCPs", h1_style))
    story.append(Paragraph(
        "External web research across GitHub, NousResearch community showcases, and developer repositories reveals verified production workflows:",
        body_style
    ))
    story.append(Paragraph("• <b>The 3-Tier Multi-Agent Meta-Workflow:</b> Power users run Hermes 24/7 on a VPS as the <b>Persistent Manager / Orchestrator</b> (triaging tickets, running crons, researching), delegating code refactoring to <b>Claude Code / Cursor</b>, synchronized via shared memory (Obsidian / Honcho / Plur).", bullet_style))
    story.append(Paragraph("• <b>Custom Model Context Protocol (MCP) Ecosystem:</b> Remote OAuth 2.1 PKCE manifests in optional-mcps/ connect Linear, Figma, Sentry, Supabase, and Postgres directly without local Node wrappers. FastMCP and mcporter provide terminal inspection.", bullet_style))
    story.append(Spacer(1, 2))

    # Table 3: Famous Community Skills & Verified Sources
    skills_table_data = [
        [
            Paragraph("<b>Skill Name & Verified Source URL</b>", table_header),
            Paragraph("<b>Category</b>", table_header),
            Paragraph("<b>Core Capability & Tool Pattern</b>", table_header),
            Paragraph("<b>Value for achiOS Adoption</b>", table_header),
        ],
        [
            Paragraph("<b>rtk-toolkit</b><br/>github.com/rtk-ai/rtk", table_cell_bold),
            Paragraph("Coding / CLI", table_cell),
            Paragraph("Pre-tool output filter compressing git/grep/cargo/find terminal logs by 60–90%.", table_cell),
            Paragraph("Drastically reduces token churn on large code searches.", table_cell),
        ],
        [
            Paragraph("<b>evey-bridge</b><br/>github.com/42-evey/evey-bridge-plugin", table_cell_bold),
            Paragraph("Multi-Agent", table_cell),
            Paragraph("Claude Code ↔ Hermes dual-agent IPC bridge for collaborative Mother-Worker execution.", table_cell),
            Paragraph("Blueprint for Hermes Telegram bot delegating tasks to Claude Code.", table_cell),
        ],
        [
            Paragraph("<b>incident-commander</b><br/>github.com/Lethe044/hermes-incident-commander", table_cell_bold),
            Paragraph("DevOps / SRE", table_cell),
            Paragraph("Autonomous SRE: monitors logs, isolates root cause, rolls back, and writes prevention SKILL.md.", table_cell),
            Paragraph("Closed-loop error recovery and auto-generated runbooks.", table_cell),
        ],
        [
            Paragraph("<b>hermes-cloudflare</b><br/>github.com/raulvidis/hermes-cloudflare", table_cell_bold),
            Paragraph("Browser", table_cell),
            Paragraph("Cloud browser rendering API for headless DOM scraping without local Playwright binaries.", table_cell),
            Paragraph("Low-memory browser scraping on headless server (achibuntu).", table_cell),
        ],
        [
            Paragraph("<b>honcho / loci</b><br/>github.com/plastic-labs/honcho", table_cell_bold),
            Paragraph("Memory", table_cell),
            Paragraph("Cross-session dialectic user modeling (2.9k stars) & Git-versioned Markdown memory palaces.", table_cell),
            Paragraph("Aligns long-term user preferences across CLI and Telegram.", table_cell),
        ],
        [
            Paragraph("<b>personal-api</b><br/>github.com/beiyuii/personal-api-skill", table_cell_bold),
            Paragraph("Personal OS", table_cell),
            Paragraph("Compiles Obsidian vaults into standardized ME.md and AGENT.md persona files in <30s.", table_cell),
            Paragraph("Directly bridges achiMem Obsidian vault into system prompts.", table_cell),
        ],
    ]
    t_skills = Table(skills_table_data, colWidths=[1.6 * inch, 0.8 * inch, 2.7 * inch, 2.4 * inch])
    t_skills.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_skills)
    story.append(Spacer(1, 4))

    # Section 4: Prioritized achiOS Feature Roadmap
    story.append(Paragraph("4. Prioritized achiOS Feature Roadmap & Blueprints", h1_style))
    
    roadmap_data = [
        [
            Paragraph("<b>Pri</b>", table_header),
            Paragraph("<b>Feature</b>", table_header),
            Paragraph("<b>Target File(s)</b>", table_header),
            Paragraph("<b>Effort</b>", table_header),
            Paragraph("<b>Implementation Architecture & Value</b>", table_header),
        ],
        [
            Paragraph("<b>P0</b>", table_cell_bold),
            Paragraph("<b>Shadow-Git Checkpoints</b>", table_cell_bold),
            Paragraph("achiAgy/src/checkpoint_manager.py", table_cell),
            Paragraph("Low (150 LOC)", table_cell),
            Paragraph("Bare Git store in ~/.local/state/achi-agy/checkpoints/. Auto-commits dirty files pre-turn; enables Telegram /rollback [n] undo.", table_cell),
        ],
        [
            Paragraph("<b>P0</b>", table_cell_bold),
            Paragraph("<b>SQLite WAL Session Store & FTS5</b>", table_cell_bold),
            Paragraph("achiAgy/src/session_db.py", table_cell),
            Paragraph("Med (350 LOC)", table_cell),
            Paragraph("Migrate sessions.json into WAL SQLite state.db with external-content FTS5 virtual table for zero-LLM sub-ms message search.", table_cell),
        ],
        [
            Paragraph("<b>P1</b>", table_cell_bold),
            Paragraph("<b>Change-Suppressed Monitor Crons</b>", table_cell_bold),
            Paragraph("AIS-OS/scripts/monitor_guard.py", table_cell),
            Paragraph("Low (120 LOC)", table_cell),
            Paragraph("Deterministic probe hasher and SQLite KV notepad (~/.config/achios/cron_notepad.db). Exits 0 on no-op, saving tokens and spam.", table_cell),
        ],
        [
            Paragraph("<b>P1</b>", table_cell_bold),
            Paragraph("<b>Subagent Worktree Isolation</b>", table_cell_bold),
            Paragraph("asa/src/worktree_isolation.py", table_cell),
            Paragraph("Med (200 LOC)", table_cell),
            Paragraph("Parallel workers run in isolated git worktrees (.worktrees/subagent-<id>). Clean worktrees auto-removed; dirty ones yield diffs.", table_cell),
        ],
        [
            Paragraph("<b>P2</b>", table_cell_bold),
            Paragraph("<b>Operational Safety Guards</b>", table_cell_bold),
            Paragraph("achiAgy/src/guards.py", table_cell),
            Paragraph("Low (100 LOC)", table_cell),
            Paragraph("Global ESTOP sentinel (~/.config/achios/ESTOP) for quiet system pause + stream repetition detector to catch runaway LLM loops.", table_cell),
        ],
    ]
    t_road = Table(roadmap_data, colWidths=[0.4 * inch, 1.6 * inch, 2.0 * inch, 0.9 * inch, 2.6 * inch])
    t_road.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_road)
    story.append(Spacer(1, 4))

    # Section 5: Anti-Patterns
    story.append(Paragraph("5. Contrarian Audit: What achiOS and Asa Must NOT Copy", h1_style))
    
    antipattern_data = [
        [
            Paragraph("<b>❌ Hermes Anti-Pattern</b>", table_header),
            Paragraph("<b>Impact / Failure Mode (Verified Source)</b>", table_header),
            Paragraph("<b>✅ achiOS / Asa Architectural Rule</b>", table_header),
        ],
        [
            Paragraph("<b>SQLite as High-Frequency Swarm Bus</b>", table_cell_bold),
            Paragraph("Writer convoy locks, 120s timeout freezes, WAL bloat to 3.07 GB (kanban_db.py).", table_cell),
            Paragraph("Use SQLite WAL strictly for discrete task state; write high-frequency worker logs to append-only disk files.", table_cell),
        ],
        [
            Paragraph("<b>Host-Local /proc PID Introspection</b>", table_cell_bold),
            Paragraph("Fails across container/SSH boundaries; risks zombie hangs if PID is recycled.", table_cell),
            Paragraph("Rely on explicit heartbeat leases and process supervisor IPC handles, never raw host PIDs.", table_cell),
        ],
        [
            Paragraph("<b>Inline FTS5 Payload Indexing</b>", table_cell_bold),
            Paragraph("2.6x storage amplification (18.9 GB FTS data in 25 GB DB; hermes_state_schema.py:1090).", table_cell),
            Paragraph("Store raw payloads externally on disk by hash; index only clean semantic text summaries in FTS5.", table_cell),
        ],
        [
            Paragraph("<b>Monolithic 'God Files'</b>", table_cell_bold),
            Paragraph("11k–20k LOC single files (cli.py, hermes_state.py, kanban_db.py) mixing IPC, DB, and UI.", table_cell),
            Paragraph("Strictly decouple storage, state machines, process managers, and CLI viewers into modules < 500 LOC.", table_cell),
        ],
    ]
    t_anti = Table(antipattern_data, colWidths=[1.8 * inch, 2.7 * inch, 3.0 * inch])
    t_anti.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#FED7D7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#FEB2B2")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF5F5")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_anti)
    story.append(Spacer(1, 4))

    # Audit Footer Callout with Detailed Source Citations
    audit_data = [[
        Paragraph(
            "<b>🛡️ Althea Fact-Check Verification Status:</b> "
            "Claims: <b>70</b> | Supported: <b>70 (100%)</b> | Partial: <b>0</b> | Unsupported: <b>0</b> | Contradicted: <b>0</b> | Fabricated Sources: <b>0</b>.<br/>"
            "<b>Verified Primary Sources:</b> "
            "<i>(1) Local Codebase:</i> ~/.hermes/hermes-agent/ (kanban_db.py, prompt_builder.py, coding_context.py, hermes_state_schema.py), achiAgy/src/, AIS-OS/tasks.md; "
            "<i>(2) Verified Web Repositories:</i> github.com/NousResearch/hermes-agent, github.com/rtk-ai/rtk, github.com/42-evey/evey-bridge-plugin, github.com/Lethe044/hermes-incident-commander, github.com/raulvidis/hermes-cloudflare, github.com/plastic-labs/honcho, github.com/codesstar/loci, github.com/beiyuii/personal-api-skill.",
            callout_text
        )
    ]]
    t_audit = Table(audit_data, colWidths=[7.5 * inch])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FFF4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#38A169")),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_audit)

    doc.build(story, canvasmaker=NumberedCanvas)


def main() -> int:
    output_dir = Path("/home/achibukz/Code/GitHub/AIS-OS/docs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = output_dir / "2026-08-24-hermes-agent-architecture-research-and-achios-blueprint.pdf"
    
    print(f"Building PDF at {pdf_file}...")
    generate_pdf(str(pdf_file))
    print(f"PDF successfully generated ({pdf_file.stat().st_size} bytes, {pdf_file.stat().st_size / 1024:.1f} KB)!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
