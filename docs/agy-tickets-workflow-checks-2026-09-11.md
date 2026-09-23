# agy-tickets author checks, September 11, 2026

These are same-session instruction walkthroughs and structural checks, not independent model benchmarks. No subagent or paid model evaluation was launched.

## Approved tracker update

Input: Aki approves the grilling decisions, asks to edit related issues, close verified completed tickets and leave unrelated work intact.

Applied output: Reused existing task/learning issues, published missing slices, and included all 43 open issues in the roadmap. Closed only achiCore #10 after comparing criteria with source and 59 passing focused tests. Kept #62 open because its passing test still permits partial unbind state. Publication proceeded under explicit authorization without another quiz.

Assessment: Matches scope and avoids equating tests or merged PRs with every acceptance requirement.

## Missing approved plan

Input: "Maybe build some automatic agents. Make tickets for whatever you think."

Expected workflow output: Ask which outcomes and authority are intended before publishing implementation tickets. Read existing context first; do not invent a full product plan or treat this as approved tracker cleanup.

Author walkthrough: The Establish scope section stops publication without an approved plan. The authorization section scopes edits separately. No issues were created for this hypothetical input.

## Standalone PR requiring live testing

Input: A reviewed PR exists outside /ToWork and requires Telegram acceptance.

Expected workflow output: Prepare a head-specific checklist. With the future queue available, submit through the shared standalone path. With only current staging available, prepare and verify it explicitly. Only SHIP auto-qualifies; nits-only requires the human bypass. Pass reaches merge readiness and does not merge.

Author walkthrough: The skill names current versus planned capability, one-slot ownership, expected/actual evidence and stale-head invalidation. It does not require a /ToWork job or claim the queue is already deployed.

## Blocked work and parallel scheduling

Input: Asa, task storage, Telegram capture and a learning pilot are requested together.

Applied output: Asa is first priority; task renderer and checklist preparation can proceed independently. Foreground reconciliation joins captured evidence with the stable task writer. Pilot fixtures can be prepared early, but final acceptance waits for the listed integrations. Shared coordinator-file changes land sequentially.

Assessment: The roadmap distinguishes hard dependencies from priority and shared-file conflicts. All new graph nodes resolve and the graph is acyclic. Existing unrelated tickets remain visible.

## Structural verification

The bundled skill validator checks frontmatter and description. A batch checker verifies all published titles/bodies, model registry keys, issue dependencies, inclusion of all open issues and local document links. Exact test outcomes and any environment limits are recorded in the planning PR.

The installed copy is checked byte-for-byte against the tracked source. This validates the installation content, not future model compliance. Runtime workflow changes remain separate implementation tickets.

## Observed validation

- Skill frontmatter validator: Skill is valid.
- Published batch validation: 30 original issue bodies matched GitHub, dependencies were acyclic, and every then-open issue appeared in the roadmap. The later CI request adds AIS-OS #49, making 31 authored issues and 43 open issues in the inventory.
- Configured AIS-OS command `/home/achibukz/.local/share/achios/venv/bin/python -m pytest tests/ -q` stopped in collection because aiohttp was missing. No assertion result was obtained from that command.
- `uv run --with pytest --with requests --with aiohttp --with pytest-asyncio python -m pytest tests/ -q` returned 491 passed, 1 warning in 33.24s. The existing warning is an unregistered real_reminders marker. CI/environment repair is AIS-OS #49.
- `scripts/run_tests.py -q tests/test_prompt_mixins.py tests/test_unbind_and_binding_uniqueness.py tests/test_orchestration_mixin.py` returned 59 passed in 0.90s in achiCore.
- No production service restart, live Telegram acceptance, Calendar mutation or provider evaluation was performed.
