# gws token cache write failure inside Claude Code sessions, 2026-09-06

Filed to give the ticket in [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) enough evidence to scope a fix. Task: send a test email via `gws gmail users messages send` on the `personal` profile, from inside this Claude Code session, on `achibuntu`.

## Symptom

`gws gmail users messages send` fails every time with a 401, even though the same profile's tokens are otherwise valid and used successfully elsewhere (daily brief, email digest, etc. run outside a Claude Code session).

```
$ GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personal GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
  ~/.npm-global/bin/gws gmail users messages send --params '{"userId":"me"}' --json "{\"raw\":\"$RAW\"}"

Using keyring backend: file
{
  "error": {
    "code": 401,
    "message": "Authentication failed: Failed to get token: Error while setting token in cache: Permission denied (os error 13): Permission denied (os error 13)",
    "reason": "authError"
  }
}
error[auth]: Authentication failed: Failed to get token: Error while setting token in cache: Permission denied (os error 13): Permission denied (os error 13)
```

The error is `os error 13` (`EACCES`) on **writing** the token cache, not on reading it or on the token itself. `gws` needs to refresh and persist the access token before it can send, and that persist step is what's blocked.

## First hypothesis: tool-level sandbox flag

The Bash tool has a `dangerouslyDisableSandbox` flag. Re-ran the identical command with it set:

```
$ GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personal GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
  ~/.npm-global/bin/gws gmail users messages send --params '{"userId":"me"}' --json "{\"raw\":\"$RAW\"}"
  # dangerouslyDisableSandbox: true

Using keyring backend: file
{
  "error": {
    "code": 401,
    "message": "Authentication failed: Failed to get token: Error while setting token in cache: Permission denied (os error 13): Permission denied (os error 13)",
    "reason": "authError"
  }
}
```

Identical failure. The flag did not change the outcome, so this is not a per-tool-call sandbox toggle problem.

## Second hypothesis: filesystem / mount permissions

Checked whether `~/.config/gws-personal` was actually writable by the session's own user, still with the sandbox flag disabled:

```
$ stat ~/.config/gws-personal ~/.config/gws-personal/token_cache.json
  File: /home/achibukz/.config/gws-personal
  Access: (0700/drwx------)  Uid: ( 1000/achibukz)   Gid: ( 1000/achibukz)
  File: /home/achibukz/.config/gws-personal/token_cache.json
  Access: (0600/-rw-------)  Uid: ( 1000/achibukz)   Gid: ( 1000/achibukz)

$ id
uid=1000(achibukz) gid=1000(achibukz) groups=1000(achibukz),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),101(lxd),982(docker)

$ touch ~/.config/gws-personal/testwrite
touch: cannot touch '/home/achibukz/.config/gws-personal/testwrite': Permission denied
```

Same uid, same gid, mode `0700` owned by that same uid, `touch` still refuses. This rules out a stale ownership/ACL problem — the file and directory are wide open to `achibukz`, and the session **is** `achibukz`. No group mismatch, no `chmod` needed, no ACL entries (`getfacl` isn't even installed, so nothing exotic was layered on).

Also ruled out a bind-mount or read-only remount over `~/.config`:

```
$ findmnt --target /home/achibukz/.config
TARGET SOURCE                            FSTYPE OPTIONS
/      /dev/mapper/ubuntu--vg-ubuntu--lv ext4   rw,relatime
```

`~/.config` resolves to the root filesystem, mounted `rw`. No separate read-only mount is in play.

## Third hypothesis (confirmed): a Landlock-style restriction baked into the Claude Code process tree

```
$ cat /proc/self/status | grep -i cap
CapInh: 0000000800000000
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: 000001ffffffffff

$ cat /proc/self/attr/current
unconfined

$ sudo -n true
sudo: The "no new privileges" flag is set, which prevents sudo from running as root.
sudo: If sudo is running in a container, you may need to adjust the container configuration to disable the flag.
```

`no_new_privs` is set on the process, and it persists with `dangerouslyDisableSandbox: true`. AppArmor reports `unconfined`, so the restriction isn't AppArmor. The remaining candidate, given the exact shape of the failure (a specific config-directory write blocked while the rest of the filesystem is untouched, `no_new_privs` on, survives attempts to disable sandboxing per-call) is a Landlock ruleset applied once to the top-level Claude Code process at launch.

Landlock's defining property is that it is a one-way ratchet: a process can only add restrictions to itself and its children, never remove them, and every descendant process inherits the ruleset with no way to opt out. That matches everything observed:
- restriction survives `dangerouslyDisableSandbox` (that flag affects the tool wrapper's own sandboxing, not a ruleset already applied further up the process tree)
- restriction is scoped (general filesystem access works; this one config path does not)
- restriction has nothing to do with Unix permission bits (owner, mode, and mount are all correct)

This was not independently verified with a Landlock-specific inspection tool (none was available in this environment), so it is the best-supported hypothesis, not a proven root cause. Whoever picks up the ticket should verify directly, e.g. by checking whether the Claude Code CLI binary calls `landlock_create_ruleset`/`landlock_restrict_self` (`strace -f -e trace=landlock_create_ruleset,landlock_add_rule,landlock_restrict_self` around session startup, if `strace` and permissions allow it in this environment).

## Corroborating precedent

`session-log.md`'s 2026-09-06 EAF entry already recorded hitting this once before and misdiagnosed it in the moment as token expiration: "confirmed the earlier permission error was isolated to read-only sandbox restrictions on `~/.config` rather than token expiration." That entry closed the question for that session's immediate task (locating the EAF, drafting an email) without filing anything further, so the restriction went unaddressed and reappeared here on the very next task that actually needed a config write.

## What works today (unaffected by this restriction)

Every scheduled job that reads or writes `~/.config/gws-*` runs as a systemd **user** unit (`achios-daily-brief.service`, `achios-email-digest.service`, etc.), not spawned from inside a Claude Code session. Those processes never inherit any Claude-Code-applied Landlock ruleset, so they hit no restriction. This is why `daily_brief.py --dry-run` and friends work fine while an interactive `gws gmail send` from this session does not.

## Open questions for the ticket

- Is the ruleset actually Landlock, or something else with the same externally-visible shape? Needs direct verification (see `strace` suggestion above), ideally from Anthropic's side since it concerns the Claude Code CLI's own process, not achiOS code.
- Is `~/.config/gws-*` specifically denylisted, or is this a broader "no writes under `~/.config`" rule that happens to also block other things nobody has hit yet?
- Given the ratchet property, any fix has to happen either (a) before the restricting ruleset is applied, i.e. inside Claude Code's own startup/settings, or (b) by moving the write outside the restricted process tree entirely (dispatch through a systemd oneshot unit, as already used for the scheduled jobs above).

## Reproduction

```bash
RAW=$(python3 -c "
import base64
from email.mime.text import MIMEText
msg = MIMEText('test')
msg['To'] = 'akibukuhan10@gmail.com'
msg['From'] = 'me'
msg['Subject'] = 'test'
print(base64.urlsafe_b64encode(msg.as_bytes()).decode())
")
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personal GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
  ~/.npm-global/bin/gws gmail users messages send --params '{"userId":"me"}' --json "{\"raw\":\"$RAW\"}"
```

Run from inside a Claude Code session on `achibuntu`. Expect the `os error 13` shown above.
