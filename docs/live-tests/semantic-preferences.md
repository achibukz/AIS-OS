# Semantic preference live test

Run this checklist with an isolated achiCore evidence directory, cohesion database,
task file and Calendar before enabling the production timer.

1. Send "Show me the file" and record the returned viewer link. Start a new turn
   and ask to see another Markdown file. Confirm it uses a viewer link. Ask "Paste
   the contents" and confirm the current request overrides the learned value.
2. Correct one linked deadline with "Keep this one out of Calendar." Confirm the
   task repair applies, the item-scoped preference is revision 1 and a replay does
   not recreate the Calendar event.
3. State a category rule for school deadlines. Confirm the category value appears
   in fresh cohesion context and does not affect quick tasks.
4. Use unclear wording such as "Do that instead." Confirm the current repair applies
   first and the receipt asks one scope question. Repeat the same Telegram update
   and confirm it creates no second question or preference event.
5. Correct and then revoke one preference. Confirm each source remains inspectable,
   revisions increase and the revoked value no longer appears in active context.
6. Submit an assistant-authored claim and a proposal whose quote is absent from the
   user message. Confirm neither activates.
7. Run `semantic_review.py` with no pending rows. Confirm `calls` is 0. Add one
   pending fixture, restart between attempts and confirm it replays from durable
   state.
8. Inspect the agy invocation. Confirm `gemini-3.8-flash`, `--effort high`, no
   `--dangerously-skip-permissions`, an empty working directory, and that a result
   with `denied_actions` is discarded. Exhaust the synthetic Manila-day budget and confirm records stay pending.

## Actual results

- AIS-OS revision:
- achiCore revision:
- Automated tests:
- Viewer and paste result:
- Placement and one-item result:
- Ambiguous scope result:
- Contradiction and revocation result:
- Tool-denial evidence:
- Restart and budget result:
- Pass, fail or skip:
