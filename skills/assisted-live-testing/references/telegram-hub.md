# Testing Grounds, reusable Telegram deployment test hub

Last inspected 2026-09-05 UTC. This is an inventory and procedure, not a claim that the hub is currently ready for another PR.

## Existing resources

| Resource | Location or identity |
|---|---|
| Private forum | Testing Grounds, chat `-1003852741563` |
| Test bot | Bot ID `8757116935` |
| Human operator | Aki, Telegram user ID `914686380` |
| Atlas | Topic `34`, bound as `atlas` during PR #154 testing |
| Operator config | `/home/achibukz/.local/state/achicore-test/operator/staging-config.json` |
| Start wrapper | `/home/achibukz/.local/state/achicore-test/operator/start-test.sh` |
| Candidate checkout at last use | `/home/achibukz/Code/GitHub/achiCore-staging-153`, detached `05cd66c` |
| Owned root | `/home/achibukz/Code/GitHub/achicore-test-153-20260905` |
| State / evidence / homes | `state/`, `evidence/`, `home/`, `codex-homes/`, `claude-homes/` beneath that root |
| Test repositories used | `achibukz/opus-subagents`, `achibukz/achicore-acceptance-153-20260905` |
| Production destinations to forbid | Bot `8999010590`, forum `-1004452093787`, state `/home/achibukz/.local/state/achicore-hub` |

The config contains a secret. Read only required fields into memory and display a redacted ownership summary, never the full file. Recheck resource identities and authorized repository scope for the new task. Authorization from an old run does not authorize an unrelated repository or destructive cleanup.

## Prepare a PR test

1. Read the candidate's `docs/autonomous-loop-staging.md` and `scripts/staging_hub.py`. Verify exact head and Python environment from the checkout used to launch it. The wrapper's printed PR label is historical text, not proof of loaded code.
2. Inspect `owner.json`, `hub.pid`, the matching process's executable/cwd and only the required staging environment fields. Confirm the root, state, bot and forum differ from production. Check persisted jobs and child-process receipts before stopping anything. The test daemon shares a host with production.
3. Create a fresh evidence directory for the new PR/head. Preserve the old run's receipts and ownership marker. Reuse existing bindings and conversations deliberately; if a case needs a fresh conversation, use an authorized product action and record it. Do not reset the whole hub.
4. If the candidate must change, stop the test daemon as described below, verify exit and back up state/homes. Use a dedicated candidate worktree at the required head; do not switch another agent's checkout. Update only the test wrapper to use the verified checkout/interpreter. Record the previous wrapper for rollback. Starting a new instance requires a distinct bot and state, not a second poller on the same token.
5. Verify provider authentication and writer/reviewer GitHub identities under the staging homes. Provision only missing required credentials through the trusted operator workflow. Copy credentials only with explicit authorization for that source and destination. Missing authentication, authorized repositories, user identity or forbidden production IDs blocks the dependent test.
6. Probe the actual worker environments before paid dispatch. A repository without `scripts/run_tests.py` needs a reviewed runner or an explicit accepted repository policy. A fabricated pass script is not a fix. Record baseline failures separately from PR failures.
7. Select the requested models through the product's supported settings and verify the actual worker engines/models. Editing a template does not change existing worker clones. `gemini-3.8-flash-high` with high effort was used in PR #154; that run did not cover Codex, Claude Code or a fallback chain.
8. Run the launcher's outbound check using the verified candidate interpreter. This sends a real staging message but proves no inbound human action. Then start one test daemon and check its logs before giving Aki the first phone action.

For the original checkout, the launcher invocation was:

```bash
cd /home/achibukz/Code/GitHub/achiCore-staging-153
.venv/bin/python scripts/staging_hub.py /home/achibukz/.local/state/achicore-test/operator/staging-config.json --outbound-check
```

Use the new verified checkout when testing a different candidate. Invoke this script with Python; its executable bit is not set. The launcher clears inherited provider variables, isolates homes/state/repositories, disables TGDB capture and enables staging background preparation/recovery. Confirm those properties in the current code.

## Console and lifecycle

Inspect without attaching:

```bash
tmux -L achicore-test list-panes -a -F '#{session_name}:#{window_index}.#{pane_index} #{pane_pid} #{pane_current_command}'
```

Attach only when the human wants the console:

```bash
tmux -L achicore-test attach -t bot
```

Detach with `Ctrl-b d`. `Ctrl-c` can stop the program; it is not detach.

The original daemon's live log is under the owned root:

```bash
tail -f /home/achibukz/Code/GitHub/achicore-test-153-20260905/state/staging-achicore-test-153-20260905.log
```

Check the actual log filename first. The older `~/.local/state/achicore-test/achicore-test.log` belongs to an earlier setup and is not proof that the current daemon is active. Redact logs before quoting them.

To stop, verify that the PID in the owned root's `hub.pid` still belongs to this staging daemon, including its process start identity. Send that PID SIGTERM and wait for exit. Inspect `state/children` and descendant process groups; do not resume or remove state while they remain alive. Afterwards the console session can be removed:

```bash
tmux -L achicore-test kill-session -t bot
```

Killing tmux alone is not evidence that detached provider processes exited. Preserve a stopped-state backup before a candidate or model configuration change. With the test session absent and wrapper verified, start it with:

```bash
tmux -L achicore-test new-session -d -s bot -n daemon /home/achibukz/.local/state/achicore-test/operator/start-test.sh
```

Leave the reusable hub intact after ordinary testing. The launcher's `--teardown` removes the run root and is only for explicitly authorized retirement after verified exit and evidence preservation.

## Human acceptance

Aki sends commands and presses buttons from his own Telegram account. A second bot cannot substitute for him. Give the exact topic and one action, then match his reply to message/job IDs and observed logs. Cover only the PR's required cases. For a concurrency claim, prove overlapping active intervals and distinct workers/worktrees/conversations; six eventual completions are not enough.

Keep separate receipts for outbound messages, simulated updates, real phone steps and real provider turns. Test Calendar, databases or other integrations against independently isolated destinations too; a staging Telegram token does not isolate those downstream systems.
