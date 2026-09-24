# Local walkthrough review

Reviewed by the skill author on 2026-09-05. These are same-session walkthroughs of the three prompts in evals.json. They are not independent model runs, a Flash benchmark or live acceptance. No provider was dispatched and no human test was simulated as real input.

## Telegram candidate change

The first decision is to resolve the PR/head and inspect the existing hub. Its wrapper label cannot establish the loaded revision. With a changed candidate, check active work, stop the owned daemon, verify children, preserve state/homes and prepare a dedicated worktree before startup. Only after probe and outbound checks pass should the assistant give Aki the first phone action. The record keeps outbound and phone evidence separate. Result of walkthrough: the skill covers this sequence; live reuse on the next PR remains not run.

## Backend queue recovery

The interface is a CLI because the human has host access. First ask for the actual runbook and service/job identifiers if missing, then provide a single scoped status command from that runbook. Do not invent a queue command or issue a destructive restart as the first step. Match operation state to the destination receipt before replay. A reported timeout does not establish that a write failed. Save the pending command and user response in Markdown. Result of walkthrough: backend access and unknown writes are covered; the real host was not contacted.

## Resume without prerequisites

The statement about a planned restart does not establish execution. The old report remains evidence for its old head. Record the missing staging credential, leave affected current-head gates blocked, and continue only independent checks. Production is not a substitute. Result of walkthrough: the skill preserves the checkpoint and has no basis to mark staging passed.

## Output review

Every case uses the Markdown interaction record and PR-comment template. Cases with blocked prerequisites can still produce a truthful blocked comment when the target PR and posting authorization are known. A missing PR means a saved draft, not an invented destination. The next evaluation is an actual assisted PR test with Aki; model-specific triggering and instruction adherence remain unverified.
