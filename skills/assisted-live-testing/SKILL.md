---
name: assisted-live-testing
description: Guide a human through live feature acceptance for a PR or change, including CLI/backend, API, browser, device and Telegram tests. Use for assisted live testing, HITL acceptance, step-by-step testing, or resuming a paused test session. Prepare and observe what tools can handle, ask for one human action at a time, and produce a Markdown interaction record plus a PR comment. Do not use for an automated-only test run or an architecture decision without an acceptance test.
---

# Assisted live testing

Work in the current assistant session. The user selects the assistant model in their client; this skill does not switch it. A requested product/test model is a separate setting. Confirm it from the running test system and preserve feature-specific engine requirements. Use Gemini 3.8 Flash when requested and supported; record an unavailable model as a missing prerequisite rather than silently substituting one.

## 1. Establish the test

Read the issue, PR, acceptance criteria, repository instructions and current diff. Pin the exact candidate head. Treat author summaries as claims to verify. If the head changes, identify affected receipts and retest those criteria against the new head.

Resolve from existing context: target PR or change, feature, environment, authorized accounts and resources, required human actions, product models, and permitted side effects. Ask only for missing information that blocks the next step. Existing authorization persists; the skill itself grants no permission to merge, deploy, message unrelated people or modify production. Never ask a user to paste a secret into chat.

Choose the smallest set of cases that can establish the requested behavior. For each, name the trigger, expected observable result, assistant work, human work and receipt. A backend test can require a CLI command, account login, physical access, an external event, or a human judgment. A frontend is not required.

Create a run ID and a Markdown record from [the record template](assets/run-record.md) outside the candidate checkout, for example under `~/.local/state/assisted-live-testing/<run-id>/`. Finish preparation when the candidate, scope and evidence plan are recorded, or name the exact missing prerequisite.

## 2. Prepare before involving the human

Inspect the existing environment and prove its ownership. Use isolated destinations and test data appropriate to the feature. Run available deterministic checks, prepare commands and fixtures, and inspect authentication by status or redacted output. Preserve active work, bindings and conversations. Record what was already broken before the candidate.

For achiCore Telegram tests, read [the Testing Grounds reference](references/telegram-hub.md) and the candidate's `docs/autonomous-loop-staging.md`. Reuse the hub only after checking its current owner, process, run root, head and active jobs. The old run ID is infrastructure history; each new PR test gets a separate evidence run ID.

For other systems, identify the equivalent service, account, database, device or CLI environment. If the assistant can run a command within the authorized scope, run it instead of making the human type it. Use the human for actions requiring their identity, access or judgment.

Do not start a human step until its prerequisites pass. A failed baseline is evidence: stop the dependent case, diagnose it and record any authorized repair. After a repair, rerun the failed check before asking the human to retry. Preserve the failing receipt.

## 3. Guide one action and verify it

Give the next action in plain language, with its exact destination or working directory, copyable command or button label, expected result, and what the user should report. Explain any consequential side effect before the action. Prefer one action per message. Bundle only inseparable steps that have no decision between them.

Example: "In the test terminal at `/path/to/checkout`, run `scripts/run_tests.py -q`. Paste the final summary and exit status. This checks the environment before we start a paid worker."

Wait for the actual reply. Being ready to restart is not evidence that a restart happened. While waiting, continue only independent preparation or observation. Match the reply to the expected case and verify available logs, state or outputs. If a reply is incomplete or contradicts the expected result, retain both and ask the smallest question that resolves it.

Record each interaction as it happens:

- UTC timestamp, case, exact instruction and purpose;
- human response, quoted or explicitly paraphrased and redacted;
- assistant command/check, exit status and receipt path;
- observed result, interpretation, and remaining uncertainty;
- wait duration and any human intervention.

Use separate evidence kinds: automated test, simulated input, live outbound, live human input, real provider turn, and user report. A user report may corroborate a result without proving every implementation detail. Record usage as `unknown` when the provider does not expose it.

If a failure occurs, classify the observed failure before proposing a retry. For an unknown external action, inspect the destination before repeating a write, push, comment, merge or release. A human tap alone does not establish whether the earlier action landed. Record fixes and head changes; never erase failed attempts or weaken assertions.

## 4. Resume and conclude

Before yielding for a human step, save the last verified checkpoint, pending instruction, owned artifacts and next safe check in the Markdown record. Another session or model can resume by reading it and revalidating current state. A pause is not a pass.

Finish with a criterion-to-receipt table using passed, failed, blocked or not run. Distinguish implementation completion, acceptance coverage and the user's decision to merge or deploy. Keep cleanup limited to recorded run-owned artifacts and the authorized scope. Stop and verify owned processes before removing their state.

Produce both outputs:

1. A redacted Markdown interaction and evidence record, including failures, human steps, exact counts and open gates. Summarize relevant interactions rather than copying the entire chat or credentials.
2. A concise PR comment from [the comment template](assets/pr-comment.md), stating the tested head, result, failures, open gates and a link to the record. Use the user's requested PR-comment output as authorization to post there. If posting has not been authorized, prepare the exact comment and request that specific authorization. If no PR exists, save the comment draft and state that there is no PR to post to.

Check the PR's current head before posting. A changed head does not inherit old evidence silently. Link an accessible report where possible. A private host link is only accessible to people on that network; keep the essential result in the comment itself. Do not modify the candidate head just to publish the report. If the API acknowledgement is lost, check existing comments before retrying. Save the posted comment URL in the local record. A failed comment post does not turn a test failure into a pass or erase the record.

For ticket authors, use [the ticket section](assets/ticket-section.md) only when a feature needs human-assisted acceptance. Keep unattended implementation and human acceptance as separate phases. Human design decisions still need a decision session, not this testing skill.
