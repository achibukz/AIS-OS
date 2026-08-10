    Project-Templates Library for achiOS

     Context
  
     This is priority #3 of Aki's 90-day plan (per CLAUDE.md): "Build a reusable project-templates library inside achiOS so new personal or 
     client projects start from a template, not from scratch." Aki opens new projects often — client mockups, internship-prep prototypes, thesis
     follow-ons, personal automations — and re-deciding scaffolding choices every time is pure tax.

     This plan defines (a) which templates ship in v1, (b) the universal docs skeleton inside each, (c) where they live, (d) how to spin up a new
      project from one, and (e) how templates plug into Aki's brainstorm → plan → frontend-skill iteration loop.

     Informing research (three parallel web-research agents, full reports saved as sibling plan files in ~/.claude/plans/):
     - uv + ruff + pytest is the 2026 Python consensus.
     - tiangolo/full-stack-fastapi-template (43k stars, Jan 2026) is the canonical FastAPI base.
     - Flask still wins for AppToSync-shape apps (server-rendered + OAuth + sessions); no dominant community template — build from official
     factory pattern.
     - Expo + obytes/react-native-template-obytes is the de facto React Native scaffold; Expo SDK 52+ ships New Architecture by default.
     - AGENTS.md + CLAUDE.md + DESIGN.md is the emerging three-layer AI-coding doc standard (donated to Linux Foundation Dec 2025; 30+ agents
     read AGENTS.md).
     - MADR 4.0 is the de facto ADR format.
     - Long architecture docs hurt AI agent performance — keep ≤300 lines, link out to ADRs.
     - Cypress is overkill for prototypes — Jest for lib/ is enough.
     - next-proto template best built fresh (promote sofiai-uiux); no community template owns the "design-focused prototype with typed mocks"
     niche.

     Workflow this enables

     The mental model Aki described:

     1. Aki: "I want to start a new project from <template>."
     2. superpowers:brainstorming runs — reads the template's AGENTS.md and docs/ so it knows what's already wired, asks only about the delta.
     3. superpowers:writing-plans produces a plan that respects the template (no re-scaffolding work that's already done).
     4. If the project has UI, invoke a frontend skill (ui-ux-pro-max, impeccable, frontend-design) — those skills fill docs/design.md and
     design/tokens.json.
     5. Implementation begins. Iterate.

     Implication for the templates: every template must (a) self-describe in AGENTS.md so brainstorming finds context, and (b) ship pre-stubbed
     PRD.md / architecture.md / design.md so skills find structure, not blank files.

     v1 template lineup

     Aki asked for 4 explicit categories + "others I can think of." Recommendation: ship six, in build order.

     ┌─────┬─────────────┬─────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────┐
     │  #  │    Slug     │                        Stack                        │                          Why ship it                           │
     ├─────┼─────────────┼─────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┤
     │ 1   │ python-lib  │ uv + ruff + pytest + mypy, src/ layout              │ Foundation — CLIs, skill backends, scripts. Used most often.   │
     ├─────┼─────────────┼─────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┤
     │ 2   │ next-proto  │ Next.js 15 + TS strict + Tailwind v4 + shadcn/ui +  │ Promote sofiai-uiux. Drop Cypress. For client/product mockups. │
     │     │             │ framer-motion + Jest                                │                                                                │
     ├─────┼─────────────┼─────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┤
     │ 3   │ fastapi-api │ FastAPI + SQLModel + Alembic + pytest + Docker      │ Default Python API. Async-first.                               │
     │     │             │ (stripped tiangolo)                                 │                                                                │
     ├─────┼─────────────┼─────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┤
     │ 4   │ flask-app   │ Flask 3 + Flask-SQLAlchemy + Flask-Migrate +        │ AppToSync shape — server-rendered apps with OAuth/sessions.    │
     │     │             │ Flask-Login + Docker                                │ Different problem than FastAPI; both belong.                   │
     ├─────┼─────────────┼─────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┤
     │ 5   │ expo-app    │ Expo SDK 52 + Expo Router + NativeWind 4 + TanStack │ React Native mobile. Forked from obytes template, i18n+auth    │
     │     │             │  Query + Zustand + Jest + Maestro                   │ stripped.                                                      │
     ├─────┼─────────────┼─────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┤
     │ 6   │ ai-chat     │ Next.js 15 + Vercel AI SDK + @ai-sdk/anthropic +    │ On-brand for Aki's AI work. Forked from vercel/ai-chatbot,     │
     │     │             │ shadcn/ui                                           │ swapped to Anthropic provider.                                 │
     └─────┴─────────────┴─────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────┘

     Skipped (with rationale):
     - Browser extension — career-ops already covers this; clone it when needed.
     - Monorepo (Turborepo/Nx) — premature; add when 3+ packages.
     - ML research scaffold — sfv-thesis is mid-flight; revisit post-thesis.
     - CLI-TS — defer; Python CLI via python-lib covers most cases.
     - t3-stack — overkill for prototypes; layer Prisma/tRPC onto next-proto when needed.

     Better to ship 6 well-maintained templates than 10 stale ones. Easy to add later.

     Universal docs skeleton (every template ships this)

     <template-root>/
       AGENTS.md           # cross-tool context, ≤200 lines, self-describes the template
       CLAUDE.md           # 5-line import: @AGENTS.md + any Claude-only overrides
       README.md           # human-facing "what this is, how to start"
       docs/
         architecture.md   # pre-filled with the template's actual structure
         PRD.md            # blank skeleton — Aki fills per project
         design.md         # blank skeleton (UI templates only)
         adr/
           0000-use-madr.md          # seed: explains MADR format
           0001-from-template.md     # auto-generated: bootstrapped from <template>@<sha>
       .gitignore
       <stack-specific files>

     Pre-stubbed section headers (research consensus):
     - architecture.md — System overview / Tech stack / Module map / Data flow / Key decisions (→ADRs) / Non-obvious constraints / Glossary
     - PRD.md — TL;DR / Problem / Users & use cases / Goals / Non-goals / Scope / User flows / Acceptance criteria / Technical notes / Open
     questions
     - design.md — Visual theme / Color / Typography / Spacing / Components / Motion / Responsive / Accessibility / Copy voice / Do's & don'ts /
     Agent prompt guide

     Hard rules baked into the skeleton:
     - Acceptance criteria must be machine-verifiable (assertions, not vibes).
     - Non-goals are mandatory — "AI cannot infer from omission."
     - architecture.md stays ≤300 lines; if it grows, split into module-local AGENTS.md files (nearest-wins).

     Where templates live

     AIS-OS/
       templates/
         README.md                 # index: lists all templates
         _docs-skeleton/           # shared starter docs/ copied into every new template
         python-lib/
         next-proto/
         fastapi-api/
         flask-app/
         expo-app/
         ai-chat/
         scripts/
           new-project.sh          # the copy script

     Source-of-truth lives here. No mirroring to separate GH template repos in v1 — adds maintenance without payoff (you're not sharing publicly
     yet).

     How you start a new project

     achiOS new <template> <project-name> [--path ~/Code/GitHub]

     What the script does:
     1. Validates <template> exists in AIS-OS/templates/.
     2. Copies the folder → <path>/<project-name>/.
     3. Substitutes placeholders ({{PROJECT_NAME}}, {{PROJECT_SLUG}}, {{AUTHOR}}, {{YEAR}}) in package.json, pyproject.toml, README.md,
     AGENTS.md.
     4. git init + initial commit.
     5. Writes docs/adr/0001-from-template.md recording template name + AIS-OS git SHA at copy time.
     6. Prints next-step hint: "run superpowers:brainstorming to scope the project."

     Implementation: Bash script at AIS-OS/templates/scripts/new-project.sh (~80 lines), invoked via a zsh function achiOS added to ~/.zshrc. No
     external deps (no copier/cookiecutter — sed placeholder substitution is enough for this scope).

     Integration with superpowers / frontend skills

     superpowers:brainstorming and superpowers:writing-plans already read AGENTS.md / CLAUDE.md by convention. Template-awareness comes from two
     markers:
     - Each template's AGENTS.md opens with ## Bootstrapped from <template> listing what's already wired (so brainstorming doesn't re-litigate
     scaffold choices).
     - docs/adr/0001-from-template.md doubles as a machine-readable marker for any future tooling.

     Frontend skills (ui-ux-pro-max, impeccable, frontend-design) write to docs/design.md and design/tokens.json (DTCG format). UI templates
     (next-proto, expo-app, ai-chat) pre-create those files as empty skeletons so skills append rather than create-from-scratch.

     No AIS-OS CLAUDE.md changes needed — skills find templates via standard file conventions. Optional later: a /new-project slash command that
     wraps the bash script.

     Build order (realistic v1 scope)

     1. Day 1 — scaffold AIS-OS/templates/ + _docs-skeleton/ + scripts/new-project.sh + templates/README.md (index).
     2. Day 2 — python-lib/ (write from scratch following 2026 conventions; no upstream to fork).
     3. Day 3 — next-proto/ (promote/clean sofiai-uiux: strip Cypress + SOFI branding + TikTok mocks; keep Jest + lib/ + docs/).
     4. Day 4 — fastapi-api/ (fork tiangolo, strip React frontend + Traefik + email).
     5. Day 5 — flask-app/ (clone AppToSync first; build from official factory pattern using AppToSync as reference).
     6. Deferred — expo-app/ (build when first mobile project lands), ai-chat/ (build when first AI app starts).

     Ship templates 1–4 as v1; defer 5–6 until first real use so they don't rot.

     Verification

     For each shipped template, end-to-end smoke test:

     achiOS new <template> smoke-test ~/tmp/
     cd ~/tmp/smoke-test
     # template-specific:
     # python-lib  →  uv sync && uv run pytest
     # next-proto  →  pnpm install && pnpm test && pnpm build
     # fastapi-api →  uv sync && uv run pytest && docker compose up
     # flask-app   →  uv sync && uv run pytest && flask --app app run

     Each must pass with zero edits. AGENTS.md populated, docs/ skeleton present, ADR-0001 generated, git initialized with one commit.

     Brainstorm-loop test: cd ~/tmp/smoke-test && claude then invoke superpowers:brainstorming — confirm it picks up the template via AGENTS.md
     and asks only delta questions (no "what language?", "what test framework?").

     Critical files to create

     - AIS-OS/templates/scripts/new-project.sh — copy + sed + git-init (~80 lines)
     - AIS-OS/templates/_docs-skeleton/AGENTS.md — universal AGENTS.md template
     - AIS-OS/templates/_docs-skeleton/docs/{architecture,PRD,design}.md — pre-stubbed doc skeletons with section headers
     - AIS-OS/templates/_docs-skeleton/docs/adr/0000-use-madr.md — MADR seed
     - AIS-OS/templates/README.md — template index
     - Per template (python-lib, next-proto, fastapi-api, flask-app): stack files + AGENTS.md + docs/ populated from skeleton

     Open decisions (resolve during execution, not blocking approval)

     - Slash command: add /new-project <template> <name> as a Claude Code skill on top of the bash script — invocable from inside Claude Code
     without leaving the chat. Recommended.
     - Shell alias: achiOS zsh function vs. direct script invocation. Recommended: zsh function.
     - Public template repos: keep in AIS-OS/templates/ only (v1) vs. also mirror to GH template repos. Recommended: AIS-OS only until you decide
      to share.