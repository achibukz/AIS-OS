---
name: agy-tickets
description: Break an approved plan into GitHub issues that Aea can implement and Luna can review, using tracer-bullet vertical slices. Writes Aki's ticket format with acceptance criteria, blockers, and a recommended model. Use when turning a plan, spec, grilling session, or PRD into implementation tickets for achibukz repos.
---

# Agy Tickets

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

The tickets you write are read by Aea, who treats the acceptance criteria as the
specification and the Blocked by section as binding, and by Luna, who audits the
resulting diff against them. Aki is usually on his phone and will not be watching.
A vague criterion produces the wrong implementation and a review that cannot catch it.

Write this skill's output to run on Sonnet or `gemini-3.7-flash-high`. Nothing here
requires Opus.

## Process

### 1. Gather context

Work from the approved plan already in conversation context, or from a plan file Aki
names. If he passes an issue reference (number, URL, or path), fetch it with
`gh issue view <n> --json number,title,body` and read the body and comments.

**If there is no plan, stop and say so.** Ask him to run `/grill-me` or
`/brainstorming` first. Tickets authored from a rough idea produce acceptance criteria
that cannot be verified, which is the failure this skill exists to prevent.

### 2. Resolve the repo

```
gh repo view --json nameWithOwner
```

Use the current workspace's repo unless Aki names another. Confirm the repo in the quiz
before publishing, because the wrong repo means the wrong agent picks the ticket up.

### 3. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of
the code. Titles and descriptions should use the project's own vocabulary and respect
existing decisions in `decisions/log.md` and any ADRs in the area you are touching.

### 4. Draft vertical slices

Break the plan into tracer bullet issues. Each issue is a thin vertical slice that cuts
through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be HITL or AFK. HITL slices need Aki in the loop for an architectural decision
or a design review. AFK slices can be implemented and merged without him. Prefer AFK.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 5. Pick a recommended model per slice

Aea runs on whichever model the ticket names. Judge the slice, not the repo:

| Slice shape | Model |
|---|---|
| Deterministic work, clear criteria, existing patterns to copy | `gemini-3.7-flash-high` |
| Ambiguous integration, unfamiliar library, design judgment inside the slice | `claude-sonnet-5` |
| Genuine architectural risk that survived the plan | flag as HITL instead |

Say why in one sentence. A ticket that names a model without a reason gets overridden.

### 6. Quiz Aki

Present the breakdown with the full body of every ticket visible, not titles alone. He
approves from his phone and cannot open a draft file. For each slice show title, HITL or
AFK, blocked by, recommended model, and the complete issue body.

Then ask:

- Does the granularity feel right, too coarse or too fine?
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the right slices marked HITL and AFK?
- Is the recommended model right on each?

Iterate until he approves. Do not publish before he does.

### 7. Ensure the labels exist

Every ticket gets `ready-for-agent` plus one `priority:` label. `gh issue create` fails
outright on a label the repo does not have, so create any that are missing first. This is
idempotent enough to run every time; ignore the "already exists" error.

```
gh label create ready-for-agent --description "Scoped tracer-bullet slice, ready for an agent to pick up" --color 0e8a16 2>/dev/null || true
gh label create priority:high --description "High priority" --color b60205 2>/dev/null || true
gh label create priority:med  --description "Medium priority" --color fbca04 2>/dev/null || true
gh label create priority:low  --description "Low priority" --color 0e8a16 2>/dev/null || true
```

Never apply `needs-triage`. It does not exist in Aki's repos and there is no triage flow
behind it.

### 8. Publish

Publish in dependency order, blockers first, so real issue numbers can go in the
Blocked by field of the tickets that follow.

```
gh issue create --repo <owner>/<repo> --title "<title>" --body-file <path> \
  --label ready-for-agent --label priority:<level>
```

Use `--body-file` rather than `--body`. Backticks and `$` in a shell-quoted body get
mangled, and a corrupted acceptance criterion is worse than a missing one.

<issue-template>
## Parent

A reference to the parent issue (only if the source was an existing issue, otherwise omit
this section entirely).

## What to build

The end-to-end behavior of this slice, in prose. Name the files and functions you expect
to change. Do not describe it layer by layer.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Unit tests cover: <the specific cases, named>

Every criterion is checkable by someone who was not in the planning conversation. "Works
correctly" is not a criterion. "Returns 429 with a Retry-After header when the quota is
exhausted" is.

The last criterion is always the test one, and it names the cases rather than saying tests
exist. Aki's standing rule is that every new feature ships with unit tests covering its
core behaviour.

## Blocked by

- #<n> <title>

Or "None (can start immediately)."

## Recommended model

`<model>`. One sentence on why.
</issue-template>

### 9. Report back

Give Aki the issue numbers and URLs in one message. Add a single line to `tasks.md`
covering the batch as a range, not one line per ticket, or the register drowns.

Do NOT close or modify any parent issue.

## Writing rules

Ticket bodies are prose Aki reads on a phone and Aea parses as a spec. Apply `unslop`:
no em dashes, no decorative bold, no mid-sentence colons, sentence case headings, active
voice. Name the concrete thing rather than reaching for an abstract noun.
