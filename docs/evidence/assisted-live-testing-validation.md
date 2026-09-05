# Assisted live-testing skill, creation and validation record

Run: assisted-live-testing-20260905. Issue: achibukz/AIS-OS #20. Source branch: `ticket/20-assisted-live-testing`, based on `efe250d`. This record concerns skill creation and local validation, not a new live product acceptance run.

## Interaction

1. Aki asked to document the existing Telegram deployment test hub, make the guided human testing reusable with Flash or another model, update ticket handoffs, audit the earlier worker test, and move the next Astra tasks toward self-learning.
2. The assistant proposed a skill in the existing conversation. It does not need a permanent agent or separate bot identity. The assistant inspected the staging launcher, operator wrapper, ownership marker and terminal metadata without printing credentials or restarting services.
3. Aki clarified that the workflow must include backend and CLI testing, not only an interface or frontend. The skill now includes human-only host access, exact command/cwd guidance and observation of unknown external writes before any replay.
4. Aki requested an MD record of the interaction and a comment on the PR. Both became standard outputs, with redaction, candidate SHA, criterion-to-receipt mapping, failures and unverified gates.
5. The assistant created a dedicated worktree and the skill source, templates, Telegram reference and retrospective. It installed the authored version locally through Skillshare, preserving existing target links. The installation is not independent approval of the skill.
6. The assistant updated the working-copy Astra plan, task list and connections inventory, preserving earlier local edits. AIS-OS #18 and achiCore #155 received assisted live-testing handoff sections without weakening acceptance criteria.

## Checks

| Check | Command or observation | Result and limit |
|---|---|---|
| Repository suite | `/home/achibukz/.local/share/achios/venv/bin/python -m pytest tests/ -q` in the isolated source worktree | 300 passed in 21.83s. Existing repository tests; not a live test of the new skill. |
| Skill scan | `skillshare audit skills/assisted-live-testing --format json` | No critical, high, medium or low findings. One informational finding for interpreter commands in the runbook. |
| Installation | `skillshare install <source>/skills/assisted-live-testing -g --yes --audit-threshold high`, then `skillshare sync -g --quiet` | Installed. Seven already-linked targets; no target entries updated or pruned. |
| Source visibility | Read installed SKILL.md through Codex, Claude Code and Antigravity paths | Contents match the authored source. Does not prove discovery in an already-open client session or a restricted topic allowlist. |
| Walkthroughs | `skills/assisted-live-testing/evals/evals.json` and `walkthrough.md` | Three same-session author reviews. No independent model execution or quantitative benchmark. |
| Existing hub | Owned run marker, PID file, tmux pane metadata and stored job stages | The original staging run exists and has no active stored jobs. Its continued existence is not readiness for a new PR. No new provider turn or real phone input was generated. |

A simple relative-link checker initially mistook the PR-comment template's `<accessible URL>` placeholder for a real file. The corrected check excludes explicit placeholders and validates actual bundled references. The template was not changed to make the check pass. Whitespace checks pass.

## Remaining acceptance

Run the skill with Aki on a real candidate and observe one complete instruction, human response, independent check, saved checkpoint and posted PR comment. Flash-specific adherence and model selection in the tested product remain unverified. CLI/backend behavior is specified and walked through, not exercised on an external host.

Production personas and their skill allowlists were not changed. A bound achiCore topic needs the skill in its allowed skills before its prompt index or scoped engine home advertises it. An ordinary client can read the installed skill directly. Neither hub was restarted for this task.
