# achiOS + achiAGY — Full System Audit

**Auditor:** Claude Opus 5
**Date:** 2026-08-20
**Method:** Direct inspection of the live `achibuntu` server (systemd state, journald, running processes, tmux panes, on-disk state files) plus source reading of `AIS-OS` and `achiAgy`. Gemini 3.7 Flash (`agy`) was used only for mechanical extraction; all analysis and conclusions here are Opus's.
**Input document:** `docs/2026-08-20-system-architecture-audit.md` is the manifest Gemini wrote *describing* the system. This is the audit it asked for. Where the manifest and the live server disagree, the server wins, and those disagreements are recorded below.

---

## 1. Verdict

The system genuinely works. Two Telegram agent bridges, nine scheduled jobs, calendar and Gmail integration, and a vault sync loop all run unattended on a headless box, and most of it does what the docs say. That is a real achievement and the architecture is sound in its bones.

But it is running **without a working safety net**, and today proved it. At 13:00 UTC a transient DNS failure knocked out four scheduled jobs. They are still sitting in `failed` state seven hours later. Aki was never told, because the alerting path depends on the exact resource whose absence it exists to report. The system failed silently and stayed failed.

That pattern — a capability that is built, documented, believed to be working, but structurally unable to fire when it matters — is the theme of this audit. There are five instances of it.

**Headline numbers**

| | |
|---|---|
| Scheduled jobs currently in `failed` state | 4 |
| Failure-alert units that also failed | 4 (100%) |
| Confirmed runtime bugs | 3 (one guaranteed crash) |
| Tests currently failing in `AIS-OS` | 44 of 222 |
| Bot processes running | 2 (one unmanaged, dies on reboot) |
| Documented-as-live components that are not installed | 1 |

---

## 2. Architecture as actually built

This is the real topology, verified against the running server — not the intended one.

```
                          ┌──────────────────────────────────────┐
                          │           TELEGRAM (7 bots)          │
                          └───────────────┬──────────────────────┘
             ┌────────────────────────────┼────────────────────────────┐
             │  TWO-WAY (agent bridges)   │   ONE-WAY (notify only)    │
             │                            │                            │
   ┌─────────▼─────────┐      ┌───────────▼──────────┐    ┌────────────▼───────────┐
   │ @achiOSClaudeBot  │      │   @achiAgyOSBot      │    │ @achiOSBot   (briefs)  │
   │ @schoMemBot       │      │   @schoMemAGYBot     │    │ @achiETFBot  (finance) │
   │  Claude Code      │      │   agy / Antigravity  │    │ @achiSchooNounceBot    │
   │  tmux -L achios   │      │   tmux -L achiagy    │    └────────────┬───────────┘
   │  tmux -L schoolmem│      │   tmux -L achiagy-   │                 │
   │                   │      │        schoolmem     │      scripts/telegram_notify.py
   │  telegram-bot.sh  │      │   achiAgy/src/bot.py │                 │
   └─────────┬─────────┘      └───────────┬──────────┘                 │
             │                            │              ┌─────────────┴─────────────┐
             │  BOT_GUARD hook            │  NO GUARD    │   9 systemd timers        │
             │  blocks schoolMem/wiki/    │  ◀── GAP     │   daily_brief, tasks,     │
             │                            │              │   email, evening, voo,    │
             └────────────┬───────────────┘              │   etf_weekly, vault_sync  │
                          │                              └─────────────┬─────────────┘
                          ▼                                            ▼
            ┌─────────────────────────────────────────────────────────────────┐
            │   FILESYSTEM: AIS-OS · achiMem · schoolMem · career-ops          │
            │   Google Calendar · Gmail · git push to origin (pre-authorised)  │
            └─────────────────────────────────────────────────────────────────┘
```

**The load-bearing observation:** every agent bridge runs `--dangerously-skip-permissions` / `bypassPermissions` with auto-approve defaulted ON, on a box that holds `gh` push credentials, Google OAuth tokens, and six other Telegram bot tokens. The only thing standing between a Telegram message and that blast radius is `ALLOWED_USER_IDS`. That is a defensible choice for a single-user personal server — but it means the whitelist check is the entire security model, and it should be treated as such.

---

## 3. What is working

Credit where it is due. These were verified live, not assumed.

- **The agy bridge is genuinely good.** `achiAgy` streams `stream-json` events from the Antigravity CLI into a rich tmux TUI while sending Telegram only the final clean answer. The separation of "verbose in the terminal, quiet on the phone" is the right call and it is implemented correctly.
- **Authorization is applied consistently.** `is_authorized()` is called at the top of all 20 command handlers, the callback-query handler, and all three input handlers (text, photo, document). I looked specifically for an ungated path and did not find one. `bot.py:215-224`.
- **Secrets were never committed.** `git log --all -- .env .env.schoolmem` is empty in `achiAgy`. `.env*` is gitignored (`.gitignore:19`). The `~/.config/achios/` secrets are correctly mode 600 in a 700 directory.
- **Timezone handling is correct everywhere.** All nine timers use explicit `Asia/Manila` in `OnCalendar`. The systemd-over-cron decision recorded in `CLAUDE.md` was the right one and it held.
- **`achiAgy`'s own test suite passes:** 43/43 in `.venv`.
- **Workspace scoping fix works.** `agy_client.py:33-45` correctly detects a broad parent directory and refuses to pass `--add-dir`, which prevents grep from scanning every repo. Good defensive engineering.
- **The tmux socket isolation is right.** Each bot gets its own tmux *server* (`-L achiagy`, `-L achios`, `-L schoolmem`), so stopping one cannot kill another.
- **`vault-sync` is the healthiest job in the system** — every 15 minutes, `Persistent=true`, and it has not failed.

---

## 4. What is broken

Ranked by what will hurt first. Every finding below was reproduced or directly observed.

---

### P0-1 · Four scheduled jobs are dead right now, and the alerting could not tell you

**Status: actively broken as of this audit.**

```
× achios-email-digest.service      failed  since 13:00 UTC
× achios-voo-digest.service        failed  since 14:00 UTC
× achios-tasks-digest.service      failed  since 15:00 UTC
× achios-evening-debrief.service   failed  since 16:00 UTC
```

Root cause, from journald:

```
NameResolutionError: Failed to resolve 'api.telegram.org'
([Errno -3] Temporary failure in name resolution)
```

A transient DNS blip. Every one of these scripts calls `telegram_notify.send()`, which does a bare `requests.post` with **no retry and no exception handling** (`scripts/telegram_notify.py:78-91`). The connection error propagates, the process exits 1, systemd marks it failed, and — because no unit sets `Restart=` — it never tries again. All four scripts run fine right now; I re-ran `tasks_digest.py` and `voo_digest.py` manually and both succeeded.

**The worse half:** all four `OnFailure=achios-failure-alert@%n.service` units *also* failed, with the identical DNS error. The failure alerter sends its alert over Telegram, so a network failure destroys both the job and the notification about the job. The alerting system is blind to the single most likely cause of failure.

This is not theoretical. It happened today, and without this audit it would have gone unnoticed until Aki wondered why his 9pm task digest never arrived.

**Fix**

1. Add retry-with-backoff inside `telegram_notify.send()` — this fixes all seven callers at once, which is why the shared-module design was correct to begin with:
   ```python
   for attempt in range(4):
       try:
           response = requests.post(..., timeout=30)
           break
       except requests.exceptions.RequestException:
           if attempt == 3:
               raise
           time.sleep(2 ** attempt * 5)   # 5s, 10s, 20s
   ```
2. Add to every scheduled `.service`:
   ```ini
   Restart=on-failure
   RestartSec=120
   ```
   Combined with `Type=oneshot`, systemd retries the whole job two minutes later.
3. **Give the failure alerter a second channel that does not depend on the network.** Minimum viable: have it also append to `~/.local/state/achios/failures.log` and write a file that the *next successful* daily brief reads and prepends ("⚠️ 4 jobs failed since the last brief"). Store-and-forward beats a second live channel.
4. Clear the current failed state: `systemctl --user reset-failed`.

---

### P0-2 · `re` is used but never imported — the HTML fallback crashes every time it runs

`src/bot.py:860`

```python
except Exception as send_err:
    logger.warning(f"HTML send failed ({send_err}), falling back to stripped plaintext.")
    plain_chunk = re.sub(r'<[^>]+>', '', chunk)     # NameError: name 're' is not defined
```

`bot.py` imports `asyncio, html, logging, os, subprocess, sys, time, pathlib, typing, psutil`. It does **not** import `re`. Verified by AST walk of the module's imports and reproduced directly:

```
CONFIRMED NameError on fallback path: name 're' is not defined
```

This is the plaintext fallback added on 2026-08-19 specifically to rescue responses that Telegram rejects for malformed HTML. It has never once worked. What actually happens when the agent produces output with an unbalanced tag:

1. `send_message` with `parse_mode=HTML` raises `BadRequest`.
2. The fallback fires and raises `NameError`.
3. That propagates to the outer `except Exception` at `bot.py:935`.
4. Aki receives `❌ Execution Exception: name 're' is not defined` — and **the entire agent response is lost**.

So the failure mode is not "slightly uglier message". It is total loss of the answer, replaced by a nonsense error. The bug is invisible in testing because it only fires on the error branch.

**Fix:** add `import re` at the top of `bot.py`. One line. Then add a regression test that feeds `split_message_chunks_html` a payload Telegram rejects and asserts the plaintext fallback delivers.

---

### P0-3 · The agy schoolMem bot can write to `schoolMem/wiki/`; the Claude one cannot

`CLAUDE.md` states the vault's provenance guarantee plainly:

> **It may never write to `wiki/`.** … That gate is therefore mechanical, not a line of instruction: `scripts/schoolmem_wiki_guard.py` is a PreToolUse hook that denies `Write`/`Edit`/`MultiEdit`/`NotebookEdit` by resolved path.

That guard is wired through `BOT_GUARD` in `scripts/telegram-bot.sh`, and it protects the **Claude Code** schoolMem bot only.

`achiAgy` has no equivalent. `grep -rn "wiki|guard|BOT_GUARD" achiAgy/src/ achiAgy/scripts/` returns **nothing**. And the schoolMem agy instance is live right now, confirmed from its tmux pane:

```
 Instance: achiagy-schoolmem
 Project: /home/achibukz/Documents/Obsidian/schoolMem
 ⚡ Auto-Approve:  ON (Bypass)
```

An agent with `--dangerously-skip-permissions`, pointed at the vault root, with no path guard. A single Telegram message like "clean up my CSOPESY notes" can write unattended into `wiki/`. The anti-hallucination guarantee — that wiki pages only ever exist because a human was in the session — is currently false for this path.

This is the highest-value finding in the audit, because it is a *silent* correctness failure in the thing the vault's entire trustworthiness rests on.

**Fix**, in order of increasing strength:

1. **Immediate:** point the schoolMem agy instance at `schoolMem/inbox/` rather than the vault root, matching what the Claude bot is allowed to touch.
2. **Proper:** implement a path guard in `agy_client.py` — before spawning, refuse any workspace that resolves inside a protected path; and if `agy` supports a deny-path hook, wire it. Mirror `schoolmem_wiki_guard.py`'s resolved-path logic including the `wiki-archive/` lookalike-sibling test that guard already handles.
3. **Strongest:** run the schoolMem bot as its own unix user with read-only access to `wiki/`. `CLAUDE.md` already names this as the real fix and defers it. It is now less deferrable.

---

### P1-4 · A second bot process is running that systemd does not know about

Two `python3 -m src.bot` processes are live:

| PID | tmux socket | Managed by | Survives reboot |
|---|---|---|---|
| 366349 | `achiagy` | `achi-agy.service` | yes |
| 3874514 | `achiagy-schoolmem` | **nothing** | **no** |

`achi-agy-schoolmem.service` exists in `achiAgy/systemd/` but is **not installed** — `systemctl --user status achi-agy-schoolmem.service` returns "could not be found". The running instance was launched by hand on 2026-08-19 and has simply not died yet.

Meanwhile `connections.md:27` claims:

> `schoolMem AGY | @schoMemAGYBot | … | live, built 2026-08-17`

Technically true this second, structurally false. The next reboot kills it permanently and nothing brings it back. Given the box has **no battery** (`CLAUDE.md` records `battery absent` — mains loss is an instant power-off), that reboot is not hypothetical.

No 409 conflict risk: the two instances load different tokens (`.env` vs `.env.schoolmem`), confirmed via `INSTANCE_NAME` in the tmux banner.

Also stale: `/tmp/tmux-1000/achiagy-ais-os-` — a dead socket with a **trailing dash**, evidence of a script that built a socket name from an empty variable. Worth finding before it produces a live orphan.

**Fix:** `achiAgy` has no `install_units.sh` equivalent to `AIS-OS`'s. Add one that does `@REPO@` substitution and installs both units, then `systemctl --user enable --now achi-agy-schoolmem.service`. Until then the docs should say "manual, not installed", not "live".

---

### P1-5 · 44 of 222 tests in `AIS-OS` are failing, all from one rename

```
44 failed, 178 passed
```

Every failure is in `tests/test_daily_brief.py`, and every one is the same error:

```
AttributeError: module 'daily_brief' has no attribute 'parse_tasks'
```

`daily_brief.py:84` defines `parse_active_tasks`. The function was renamed and the test file was never updated. The entire daily-brief test suite has been dead ever since — and `CLAUDE.md` explicitly says:

> Tests: `tests/test_daily_brief.py`. Keep them passing when the format changes.

So the brief — the single most user-visible output of the whole system — currently has **zero** effective test coverage, while appearing to have 44 tests. A green-looking suite that is entirely red is worse than no suite, because it buys false confidence.

**Fix:** sed `parse_tasks` → `parse_active_tasks` in the test file, re-run, and fix whatever real regressions that exposes. Then add `pytest` to the vault-sync job or a pre-push hook so this cannot rot silently again.

---

### P1-6 · Token accounting is producing impossible numbers

Live from `sessions.json`, one project, `turn_count: 14`:

```json
"output_tokens":   56650784,      // 56.6 MILLION
"thinking_tokens": 20012228,      // 20.0 million
"last_turn_output_tokens": 16389  // last turn: 16k
```

14 turns at ~16k output each is roughly 230,000 tokens. The stored total is **246× higher**.

The cause is at `session_manager.py:337-342`:

```python
if in_tok:
    p_state.input_tokens = in_tok          # ← assignment (fixed 2026-08-19)
if out_tok:
    p_state.output_tokens += out_tok       # ← still accumulating
if think_tok:
    p_state.thinking_tokens += think_tok   # ← still accumulating
```

The 2026-08-19 fix that stopped sliding-context accumulation was applied to `input_tokens` only. `output_tokens` and `thinking_tokens` still use `+=` on a value that appears to already be conversation-cumulative, so it compounds. This is the *same bug* that produced the bogus 1.65B input figure, half-fixed.

Impact is limited to display — `/usage` and `/context` report fiction — but `/usage` exists precisely so Aki can decide when to `/new` before hitting quota. A metric that is 246× off is worse than absent.

**Fix:** mirror the input-token treatment (assign, track a separate peak/lifetime if a true lifetime is wanted), and add a sanity assertion in `test_session_metrics.py` that no per-turn delta exceeds the model's `max_out` from `MODEL_REGISTRY`. The registry already has the bound; use it.

---

### P1-7 · Nothing guards against two prompts at once

`bot.py:1010-1011`, and identically at 953, 964, 1032, 1052:

```python
task = asyncio.create_task(execute_agent_pipeline(update, user_text))
active_tasks[chat_id] = task
```

There is no check for an already-running task before overwriting the slot. Send a second message while the first is still streaming and:

1. A **second `agy` subprocess spawns** against the same `conversation_id`, with both writing to the same workspace under `--dangerously-skip-permissions`. Two agents editing the same files concurrently.
2. The first task's handle is **overwritten and lost**, so `/cancel` (`bot.py:621`) can no longer reach it. It becomes unkillable except by restarting the daemon.

On a phone, sending a follow-up before the previous answer lands is the *normal* thing to do, so this is easy to trigger by accident.

**Fix:**

```python
existing = active_tasks.get(chat_id)
if existing and not existing.done():
    await update.message.reply_text(
        "⏳ Still working on the previous message. /cancel to abort it first."
    )
    return
```

Better still, a per-chat `asyncio.Lock` plus a bounded queue so follow-ups are serialised rather than rejected.

---

### P2-8 · `sessions.json` is written non-atomically

`session_manager.py:181-187` opens the real path with `"w"` — truncating it — then serialises. A crash, OOM kill, or power loss between truncate and flush leaves a zero-length or half-written JSON file. `_load()` catches the resulting exception (line 177) and logs it, then silently starts with **no sessions at all**: every project's `conversation_id`, turn count, and model preference gone.

Given the box has no battery and loses power instantly, this is a realistic loss.

**Fix:** write to `sessions.json.tmp`, `os.replace()` onto the target. `os.replace` is atomic on POSIX. Three lines.

---

### P2-9 · Runtime state is being written into a git working tree

`.env` sets `STATE_DIR` to the repo root, so `config.py:37` resolves state into `~/Code/GitHub/achiAgy/` rather than `~/.local/state/achi-agy/`. Result:

```
achiagy.log     9.4 MB   and growing, never rotated
attachments/    3.1 MB   every photo and file ever sent, never pruned
sessions.json   live state, in the repo
```

There is a **stale duplicate** at `~/.local/state/achi-agy/sessions.json` (354 bytes, 2026-08-17) that nothing reads any more — a trap for the next person who debugs session state.

All three are gitignored so nothing leaks, but state belongs outside the tree the agent itself edits. And `achi-agy.service` declares `StandardOutput=append:%h/.local/state/achi-agy/bot.log`, so the unit and the app disagree about where state lives. Note the schoolMem env sets `INSTANCE_NAME` but no `STATE_DIR`, so the two instances behave differently — that inconsistency is the real smell.

**Fix:** drop `STATE_DIR` from `.env`, let `config.py`'s default win, delete the stale duplicate, and add a `logrotate` or a size check. There is no rotation configured anywhere on this box for any achi log.

---

### P2-10 · `Persistent=true` plus non-idempotent sends means duplicate messages after downtime

Seven timers set `Persistent=true`, which is correct for a box that loses power. But on boot, systemd fires every missed activation. `tasks_digest` has five daily triggers; a day of downtime means Aki's phone gets a burst of stale digests on power-up.

Worse, `telegram_notify.send()` raises `SystemExit` on a non-OK response *mid-loop* (`telegram_notify.py:88`). If message 2 of 3 fails, messages 1 is already delivered and there is no resume — a retry re-sends message 1.

**Fix:** have each job stamp a last-run marker (date + slot) in `~/.local/state/achios/` and skip if the slot is already satisfied and more than a few hours stale. Make retry safe before adding `Restart=on-failure` from P0-1, or the retry will duplicate.

---

### P2-11 · Bot tokens are being written to journald in cleartext

From `journalctl --user`:

```
Failed to send Telegram alert: HTTPSConnectionPool(host='api.telegram.org', port=443):
Max retries exceeded with url: /bot8725294836:AAFyEDmLBcTS-vlaMb66JcpVYnPCEKYX1dQ/sendMessage
```

`requests` embeds the token in the URL path, and the exception string carries it into the log. The token for `@achiOSBot` is now in the journal in cleartext, readable by anything that can read the user journal, and it will persist for the journal's retention period.

Related: `achiAgy/.env` and `.env.schoolmem` are mode **644** (world-readable), while `~/.config/achios/*.env` are correctly **600**. Any local process can read the agy bot tokens.

**Fix:**
1. `chmod 600 ~/Code/GitHub/achiAgy/.env*`
2. Catch `RequestException` in `telegram_notify.send()` and re-raise with the token redacted — this falls out naturally from the P0-1 retry work.
3. Rotate the `@achiOSBot` token via BotFather, since it is now in a log.

---

### P2-12 · The `/asa` skill is broken

`~/.claude/skills/asa/SKILL.md` documents a CLI (`asa run`, `asa result`, `asa status`) and instructs the agent not to reimplement it in bash. That binary **does not exist** anywhere — not on `PATH`, not in `~/.local/bin`, not in the skill directory, which contains only `SKILL.md`.

I hit this during this audit: the dispatch appeared to succeed and returned exit 0 while doing nothing, because the failure was swallowed. Any future session invoking `/asa` will silently produce no workers.

**Fix:** either write the `asa` CLI, or delete the skill. A skill that documents a missing binary is worse than no skill — it fails in the least visible way possible.

---

### P3-13 · Docs drift

`CLAUDE.md` is the authoritative description of this system and it does not mention `achiAgy` **at all**. Every architectural rule it states — the two-bot model, the `BOT_GUARD` contract, "one bot per repo rather than one routing between them" — was written before a second agent runtime existed. A fresh session reads `CLAUDE.md`, believes there are two bots, and is wrong by a factor of two.

Concretely missing:
- No `## achiAgy` section describing the agy bridge, its units, its tmux sockets, or its model registry.
- The **Telegram bots** table lists two bots; there are seven identities in `connections.md` and four agent bridges.
- The `BOT_GUARD` discussion asserts the wiki guard protects the vault. Per P0-3 it protects one of two bots that reach it.
- `connections.md:27` marks `@schoMemAGYBot` "live" when its unit is not installed.
- The default workspace is `~/Code/GitHub` (`config.py:47`), the broad parent that `agy_client.py` then warns about and refuses to scope. The live session is sitting in it right now (`"active_project": "GitHub"`). Default should be a real repo.

**Fix:** add the `achiAgy` section to `CLAUDE.md`, correct the bots table, and mark schoolMem AGY accurately in `connections.md`.

---

## 5. Fix plan

Ordered so that each step is safe given the ones before it. Note the deliberate sequencing in Day 1: idempotency lands *before* retry, or retry will spam duplicates.

### Day 1 — stop the bleeding (~1 hour)

| # | Fix | Where | Effort |
|---|---|---|---|
| 1 | `import re` | `achiAgy/src/bot.py:1` | 1 min |
| 2 | `systemctl --user reset-failed` | shell | 1 min |
| 3 | `chmod 600 achiAgy/.env*` | shell | 1 min |
| 4 | Concurrency guard before `create_task` | `bot.py` ×5 sites | 15 min |
| 5 | Atomic `os.replace` for `sessions.json` | `session_manager.py:181` | 5 min |
| 6 | Last-run markers (idempotency) | the 5 digest scripts | 20 min |
| 7 | Retry + backoff + token redaction | `telegram_notify.py:78` | 20 min |
| 8 | `Restart=on-failure` / `RestartSec=120` | 7 `.service` files | 10 min |

### Week 1 — close the guarantees

| # | Fix | Why |
|---|---|---|
| 9 | Point schoolMem agy at `inbox/`, then build the path guard | P0-3 — the vault's provenance guarantee is currently false |
| 10 | Store-and-forward failure alerting | P0-1 — alerting must survive the network |
| 11 | Fix `parse_tasks` → `parse_active_tasks`, get 222/222 green | P1-5 — the brief has no real coverage |
| 12 | Install `achi-agy-schoolmem.service` via a repo `install_units.sh` | P1-4 — orphan dies on the next power cut |
| 13 | Fix output/thinking token accumulation + registry-bound assertion | P1-6 — `/usage` is 246× wrong |
| 14 | Rotate the `@achiOSBot` token | P2-11 — it is in journald |

### Week 2 — structural

| # | Fix |
|---|---|
| 15 | Move `STATE_DIR` out of the repo; delete the stale duplicate; add log rotation for all achi logs |
| 16 | Write `CLAUDE.md`'s `achiAgy` section; correct the bots table and `connections.md` |
| 17 | Change `DEFAULT_WORKSPACE` from `~/Code/GitHub` to a real repo |
| 18 | Build the `asa` CLI or delete the skill |
| 19 | Clean the stale `achiagy-ais-os-` socket and find the script that made a name with a trailing dash |

---

## 6. The one architectural change worth making

Every finding in section 4 traces back to a single structural fact: **there are four agent bridges and nine scheduled jobs, and each one carries its own copy of the concerns that should be shared.** Two independent Telegram send paths with different chunking and different escaping. A wiki guard that exists in one runtime and not the other. Token accounting fixed in one field and not its neighbours. State that lives in two places, one of them stale.

The fix is not to add a fifth bridge. It is to make **one shared layer that every bridge and every job must go through** for the three things that keep going wrong:

1. **Sending to Telegram** — one implementation, with retry, chunking, escaping, and redaction. `telegram_notify.py` is already that module; `achiAgy` should use it instead of its own path.
2. **Writing to a protected path** — one resolved-path guard, enforced by both runtimes, not one hook wired into one bash script.
3. **Persisting state** — one atomic-write helper, one state directory.

Aki already had the right instinct here — the docstring in `telegram_notify.py` says *"Import it rather than re-implementing the send — one place holds the credential contract."* That rule was correct and `achiAgy` simply did not inherit it, because it was built as a separate repo. Extending the rule across the repo boundary is the whole change.

Concretely: extract those three concerns into a small `achios-core` module that both repos import. That single move closes P0-1, P0-3, P2-8, P2-9, and P2-11 at the source, and stops the next bridge from reintroducing them.

---

## 7. Verification commands

```bash
# current failure state
systemctl --user --failed
journalctl --user -u achios-tasks-digest.service -n 30

# prove the re bug
cd ~/Code/GitHub/achiAgy && python3 -c "exec(\"re.sub('a','b','c')\")"

# test suites
cd ~/Code/GitHub/AIS-OS  && ~/.local/share/achios/venv/bin/python -m pytest tests/ -q
cd ~/Code/GitHub/achiAgy && .venv/bin/python -m pytest tests/ -q

# running bots (expect 2, one unmanaged)
pgrep -af "src.bot"
ls -la /tmp/tmux-1000/

# token accounting
python3 -m json.tool ~/Code/GitHub/achiAgy/sessions.json | grep -E "turn_count|output_tokens"

# secret exposure
journalctl --user | grep -c "api.telegram.org/bot[0-9]"
stat -c '%a %n' ~/Code/GitHub/achiAgy/.env*
```

---

## 8. Findings index

| ID | Severity | Finding | File |
|---|---|---|---|
| P0-1 | Critical | 4 jobs failed; alerting shares the failed dependency | `telegram_notify.py:78`, all `.service` |
| P0-2 | Critical | `re` used, never imported — fallback always crashes | `bot.py:860` |
| P0-3 | Critical | agy schoolMem bot can write `wiki/`; no guard | `achiAgy/src/*` (absent) |
| P1-4 | High | Unmanaged second bot; unit not installed | `achiAgy/systemd/` |
| P1-5 | High | 44 tests dead from a rename | `tests/test_daily_brief.py:25` |
| P1-6 | High | Token totals 246× wrong | `session_manager.py:337` |
| P1-7 | High | No concurrency guard; `/cancel` loses the handle | `bot.py:1010` |
| P2-8 | Medium | Non-atomic `sessions.json` write | `session_manager.py:181` |
| P2-9 | Medium | State in git tree; 9.4MB unrotated log | `config.py:37`, `.env` |
| P2-10 | Medium | `Persistent=true` + non-idempotent = duplicates | timers + `telegram_notify.py:88` |
| P2-11 | Medium | Tokens in journald; `.env` mode 644 | journald |
| P2-12 | Medium | `/asa` skill documents a nonexistent binary | `~/.claude/skills/asa/` |
| P3-13 | Low | `CLAUDE.md` never mentions `achiAgy` | `CLAUDE.md`, `connections.md:27` |
