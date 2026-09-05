## Assisted feature live testing

Include this section only when automated checks cannot establish the required behavior. Implementation may remain unattended. Name the specific CLI/backend, API, browser, device, account or Telegram action that needs the human.

- Candidate: PR and exact head, filled in when ready.
- Environment: named isolated service, test account, worktree or device; prerequisite owner.
- Assistant prepares: baseline checks, fixtures, commands and observation tools.
- Human performs: exact action requiring their access or judgment.
- Cases: trigger, expected observable result and failure cases.
- Test models: actual product models/engines required by the acceptance criteria.
- Boundaries: allowed mutations, forbidden destinations, stop and cleanup rules.
- Outputs: Markdown interaction/evidence record and a comment on the tested PR.

Invocation to fill in when handing over the PR:

> Use assisted-live-testing for PR <URL> at <SHA>. Verify <named criteria> in <environment>. Use <product model/engine, if relevant>. Prepare everything you can, then guide me one step at a time through <human actions>. Verify my results against <logs/state/output>. You may <authorized test actions>; stop before <excluded actions>. Save a redacted Markdown record of our interaction and receipts, and post the result as a comment on this PR. Keep simulation and real observations separate, and leave unverified gates open.

The assistant model can be Astra, Gemini 3.8 Flash or another model selected in the client. A test requiring a particular product model still has to exercise that model.
