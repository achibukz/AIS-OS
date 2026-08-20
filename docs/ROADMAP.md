# achiOS roadmap

What is worth building next, and why. Written 2026-08-21, after the self-learning loop v2
build and the infrastructure audit.

Ordered by expected value, not by effort. Each item says what is wrong today, what "better"
looks like, and how you would know it worked. Anything already tracked as a dated task lives
in `tasks.md`; this file is for the things that need thinking about before they become tasks.

Sources: `docs/2026-08-20-opus-audit-achios-achiagy.md`,
`docs/2026-08-20-opus-audit-learning-loop.md`,
`docs/superpowers/specs/2026-08-20-self-learning-loop-design.md`.

---

## 1. Close the second memory writer

**Today.** The agy model writes to memory through the `memory_engine` CLI whenever it feels
like it. Since 2026-08-21 those writes are logged (`source: cli`), so you can see them. But
nothing gates them, nothing caps them, and nothing checks them against the rules the loop
already wrote. The gate governs one of the two paths into memory.

**Better.** Either route CLI writes through the same gate the loop uses, or make the model's
tool a proposal rather than a write, landing in the ledger as `pending` for the next review
to judge. The second option is closer to how Hermes works and keeps one decision-maker.

**Know it worked.** Every record in the ledger has a verdict. `external` drops to zero
without memory becoming less useful.

**Depends on.** The 2026-08-27 audit. If most writes turn out to be `source: cli`, this
becomes the highest priority item on this list rather than the first of several.

---

## 2. Fix recall: the loop cannot learn facts

**Today.** Capture only fires on ~21 hardcoded trigger phrases. `my thesis adviser is Briane
Paul V. Samson` is a durable fact, and the loop is structurally blind to it because no
trigger word appears. It learns preferences phrased a particular way and nothing else.

**Better.** Three options, cheapest first:

- Widen the trigger list. Cheap, but it is guessing, and every new phrase raises gate volume.
- Drop the prefilter for short messages and let the gate judge everything under some length.
  Costs one gate call per review regardless, since cost is per call, not per candidate.
- Have the gate read the whole turn rather than one line, which also fixes multi-turn
  preferences (spec §11).

The second is probably the right first move: the prefilter exists to save money, and the
money it saves turns out to be near zero.

**Know it worked.** Re-run the recall check from the day-7 audit. State five durable facts
across a week and count how many were captured.

---

## 3. Make alerting survive the thing it reports on

**Today.** Partly fixed. `telegram_notify.send()` now retries and the six scheduled units
restart on failure. But the `OnFailure=achios-failure-alert@` units still deliver over the
same network path as the job that failed. A long outage still means no job and no alarm,
just a quieter version of it.

**Better.** Store and forward. A failed alert writes to a spool file; the next successful
run drains it. Then an outage delays the alert instead of destroying it.

**Know it worked.** Drop DNS for ten minutes over a scheduled run, restore it, and confirm
the alert arrives late rather than never.

---

## 4. Rotate the leaked bot token

**Today.** `@achiOSBot`'s token is sitting in journald in cleartext from before the
redaction fix. Redaction stops new leaks; it does not unwrite the old ones. Journald is
local and the box is single-user, so this is not urgent, but it is real.

**Better.** Rotate via BotFather, update `~/.config/achios/telegram.env`, vacuum the old
journal entries. Also `chmod 600` the `achiAgy/.env*` files, which were never tightened.

**Know it worked.** `journalctl --user | grep <old-token-prefix>` returns nothing, and the
jobs still send.

---

## 5. Repair the daily-brief test suite

**Today.** 44 tests in `tests/test_daily_brief.py` fail, all with
`module 'daily_brief' has no attribute 'parse_tasks'` — the function was renamed to
`parse_active_tasks` and the tests were never updated. The daily brief is the single most
user-visible piece of achiOS and it currently has no working regression net.

**Better.** Update the call sites. It is close to mechanical, which is exactly why it keeps
getting skipped.

**Know it worked.** `pytest -q` reports zero failures, so a real regression becomes visible
instead of hiding inside a wall of red.

---

## 6. Concurrency guard in achiAgy

**Today.** `execute_agent_pipeline` starts a task per message with no guard. Two messages
sent quickly run two agent pipelines against the same session state, and the last writer
wins. With the self-learning loop now mutating `turns_since_review` and writing memory from
the same path, the blast radius is larger than it was when the audit found it.

**Better.** A per-chat lock, or queue turns and tell the user their message is queued.

**Know it worked.** Send three messages in one second and confirm the turn counter advances
by exactly three.

---

## 7. Ledger hygiene

**Today.** `learning_ledger` never prunes, and `_latest_by_id` parses the whole file on
every call. At current volume that is fine for months. It is a slow leak, not a bug.

**Better.** Roll the file monthly into `archives/`. Do it when the audit needs a clean
window anyway, not before.

**Know it worked.** Ledger reads stay flat as the archive grows.

---

## 8. Memory budget pressure

**Today.** `USER.md` sits at 1706 of 2500 characters. When a file fills, the loop replaces
the **oldest** entry to make room — and in `USER.md` the oldest entry is the Identity line.
An autonomous write can therefore overwrite who you are with a formatting preference, with
no warning.

**Better.** Two changes worth having independently. Refuse to replace an entry that was
written by hand rather than by the loop, which the `source` field now makes possible. And
alert at 90% rather than failing silently at 100%.

**Know it worked.** Fill `USER.md` to the ceiling in a sandbox and confirm the Identity
entry survives.

---

## Ideas not yet worth doing

Kept so they are not rediscovered from scratch.

**Per-chat write budgets.** The daily cap is global. With one user this is theoretical.

**Semantic dedup.** The loop can write the same preference twice in different words. The
budget ceiling forces a `replace` eventually, so it self-corrects. Worth revisiting only if
the audit shows duplicates crowding out real rules.

**Multi-turn candidate context.** Spec §11. Deferred to the day-7 audit deliberately, and
partly subsumed by item 2 above.

**Cleaning the 6 poisoned tgdb notes.** Nothing reads tgdb for learning any more, so they
are inert historical record. Rewriting vault history for no functional gain is not worth it.

**Running the bots as separate unix users.** The real fix for schoolMem's wiki guard, which
is currently a heuristic over Bash. Only worth it if unattended wiki writes become a genuine
problem.
