# Self-learning loop: how to test it

Written 2026-08-21. Covers Task 8 steps 2 to 4 of
`docs/superpowers/plans/2026-08-20-self-learning-loop-v2.md`, the part that needs you
on your phone.

Everything else in the plan is done and verified. What is still unproven is the live
path: a real Telegram turn reaching `capture_candidate`, the turn counter tripping at
ten, and the review writing to memory. A sandboxed run already proved the chain works
against the real gate. This proves the wiring.

## What you are testing

Three things, in order. If one fails the later ones cannot pass, so read the results in
sequence rather than jumping to the end.

1. **Capture.** Does a preference you type reach the ledger as `pending`?
2. **Trigger.** Does the review actually fire on the tenth turn?
3. **Write.** Does the gate classify it `durable` and land it in memory?

## Before you start

Run these on the box. All three should pass before you send anything.

```bash
systemctl --user is-active achi-agy.service          # expect: active
tmux -L achiagy capture-pane -p -t bot | tail -5     # expect: ● Active & Polling
~/.local/share/achios/venv/bin/python -c "
import sys, os, json; sys.path.insert(0, os.path.expanduser('~/Code/GitHub/AIS-OS/scripts'))
import learning_ledger as ll; print(json.dumps(ll.stats(), indent=2))"
```

The ledger should read all zeros on a first run. If it does not, that is fine, it just
means a previous test left records. Note the numbers so you can tell new from old.

## The test

Open `@achiAgyOSBot` and send **ten messages**. Nine can be anything. Make one of them a
real preference, and put it somewhere in the middle rather than last, so you can see the
counter reach ten after it.

Use this exact line as the preference, because it is known to classify cleanly:

```
never use bullet points when you reply to me
```

Nine filler messages, anything like `what is 2+2`, will do. What matters is that ten
turns complete. A turn only counts if the bot actually replies. A turn that errors,
times out, or that you cancel increments nothing, so if the bot fails on one, send an
extra to make up for it.

### Why ten

`REVIEW_INTERVAL` is 10. The counter lives on the project state, per project, and resets
to zero each time the review fires. Capture happens on every turn; the review is what
waits for ten.

## Checking the result

Paste this. It prints the ledger and both memory files together, which is what you want,
because a rule can legitimately land in either one.

```bash
~/.local/share/achios/venv/bin/python - <<'EOF'
import sys, os, json
sys.path.insert(0, os.path.expanduser('~/Code/GitHub/AIS-OS/scripts'))
import learning_ledger as ll
from pathlib import Path

print("=== LEDGER ===")
print(json.dumps(ll.stats(), indent=2))
for r in ll._latest_by_id(None).values():
    print(f"{r['state']:8} | target={str(r.get('target')):6} | {r['raw'][:45]!r}")
    if r.get('rule'):
        print(f"{'':8} -> {r['rule']}")
    if r.get('reason'):
        print(f"{'':8} reason: {r['reason']}")

for name in ("MEMORY.md", "USER.md"):
    p = Path.home() / ".config" / "achios" / name
    print(f"\n=== {name} ===")
    print(p.read_text().strip() if p.exists() else "(missing)")
EOF
```

### What a pass looks like

The bullet-points line appears as `written`, with a rule along the lines of
`Never use bullet points in responses.`, and that rule is present in one of the two
memory files.

**Check both files.** The gate routes anything about who you are or how you want to be
spoken to into `USER.md`, and everything else into `MEMORY.md`. The bullet-points rule is
about how you want to be spoken to, so it will almost certainly be in `USER.md`. That is
correct behaviour, not a bug. I tripped over this myself during verification.

Your filler messages should not appear in the ledger at all. They are dropped by the
prefilter before anything is recorded, which is the intended behaviour and the reason the
loop is cheap to run.

## If something did not happen

| Symptom | Cause | What to do |
|---|---|---|
| Ledger completely empty | The prefilter never matched | Your wording had no trigger phrase. See the list below. |
| Record stuck at `pending` | Review has not fired yet | You have not completed ten turns since the last review. Send more. |
| Still `pending` after 10+ turns | Gate call failed | `grep -i "gate\|review" ~/.local/state/achios/*.log`. A failed gate leaves records pending on purpose so the next review retries them. |
| `rejected`, reason `one_off` | The gate judged it not durable | Working as designed. Rephrase as a standing rule and try again. |
| `rejected`, reason `invalid_rule` | Model returned junk or `N/A` | Validation caught it. Not a problem unless it repeats. |
| `rejected`, reason `rate_capped` | Hit 3 writes per review or 10 per day | Wait for tomorrow or raise the caps in `background_review.py`. |
| `rejected`, reason `budget_full` | Memory is at its 2500-char ceiling | Remove an entry by hand, see rollback below. |
| Written, but the rule is wrong | Gate misjudged it | Remove it, note it, this is exactly what the day-7 audit is for. |

### The trigger phrases

Capture only happens if your message contains one of these, case-insensitive:

```
banned, don't use, do not use, never use, stop using, avoid using, not use,
less formal, more casual, too formal, take note, make sure to, remember that,
always make sure, rule:, change the, replace the, update the, my favorite,
i prefer, always use
```

This is a known limitation and worth understanding before you judge the loop. A durable
fact with no trigger phrase is never captured. During verification,
`my thesis adviser is Briane Paul V. Samson` was dropped entirely, because none of those
strings appear in it. The loop currently learns preferences phrased with trigger words
and misses plain statements of fact. Whether that is acceptable is the recall question
for the 2026-08-27 audit.

## Limits currently in force

| Setting | Value | Where |
|---|---|---|
| Turns between reviews | 10 | `ACHIOS_REVIEW_INTERVAL` env, or `background_review.py` |
| Writes per review | 3 | `MAX_WRITES_PER_REVIEW` |
| Writes per day | 10 | `MAX_WRITES_PER_DAY` |
| Candidates per gate call | 25 | `MAX_CANDIDATES_PER_REVIEW` |
| Memory budget | 2500 chars per file | `memory_engine.py` |

### One thing to watch on the budget

As of 2026-08-21, `USER.md` holds 1667 of its 2500 characters and `MEMORY.md` holds 207.
There is room, so this will not bite during the trial.

It matters later. When a write would exceed the budget, the loop does not give up. It
replaces the **oldest** entry to make room. In `USER.md` the oldest entry is your Identity
line. So once that file fills up, an autonomous write can silently overwrite who you are
with a formatting preference. Nothing warns you.

Keep an eye on the number:

```bash
~/.local/share/achios/venv/bin/python -c "
from pathlib import Path
for n in ('MEMORY.md','USER.md'):
    p = Path.home()/'.config/achios'/n
    print(n, len(p.read_text()), 'of 2500')"
```

If `USER.md` gets past roughly 2300, prune it by hand before the loop does it for you.
This is on the list for the day-7 audit.

One gate call costs roughly 20k input tokens and about 7 seconds, and that cost is per
call rather than per candidate. Batching is why the prefilter can afford to be generous.

## Turning it off or undoing a write

Kill switch, no redeploy and no code change:

```bash
systemctl --user set-environment ACHIOS_REVIEW_INTERVAL=0
systemctl --user restart achi-agy.service
```

Remove a single bad rule:

```bash
~/.local/share/achios/venv/bin/python ~/Code/GitHub/achiAgy/src/memory_engine.py \
  remove --target user --text "<a substring of the rule>"
```

Use `--target memory` if it landed in `MEMORY.md` instead.

v1's original data, if you ever need it back, is in
`archives/2026-08-20-harvester-rollback/`.

## What to write down for the audit

The ledger is append-only, so nothing you do here destroys evidence. Over the trial week,
the four questions on 2026-08-27 are:

1. Of everything marked `written`, how much is genuinely a durable preference? That is
   precision.
2. Of the preferences you actually stated that week, how many got captured? That is
   recall. Compare against `achiMem/tgdb/` for the week.
3. How many gate calls fired, and what did the week cost at roughly 20k tokens each?
4. Did any write need reverting?

Then decide: leave it autonomous, add a Telegram confirmation step before each write, or
fall back to `/learn` only.
