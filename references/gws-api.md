# gws — Google Workspace CLI

Binary on Mac: `/opt/homebrew/bin/gws`.
Binary on Linux (Achibuntu): `~/.npm-global/bin/gws` (`npm install -g @googleworkspace/cli`).
Shape: `gws <service> <resource> [sub-resource] <method> --params '<JSON>' [--json '<body>']`.
Services in use here: `gmail`, `calendar`.

## Linux (Achibuntu) setup

`gws` is installed and verified across all four accounts under `~/.config/gws-*` using `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file`.
Hermes Google Workspace OAuth is also wired and live through token files:

- `~/.hermes/google_token.json` — personal token, currently `akibukuhan10@gmail.com`; sees Gala, Personal, Bdayy, DLSU, Job (reader), CSOPESY, PEDFOUR, STCLOUD, STSP001, THS-ST1, Canvas import, LSCS, and DLSU primary as free/busy.
- `~/.hermes/gws-work/google_token.json` — work token, `akibukzwork@gmail.com`; sees Job as primary/owner plus ING, Family, Holidays PH, and shared school calendars.

Use this script for upcoming events across all visible personal + work calendars:

```bash
~/.hermes/scripts/gcal_upcoming.py --days 14 --max 50
~/.hermes/scripts/gcal_upcoming.py --days 14 --max 50 --json
```

Verified 2026-08-16 from Hermes: personal and work Google live checks OK, work Gmail profile returns `akibukzwork@gmail.com`, ING calendar is visible, and upcoming ING events are returned. The default Hermes `google_api.py calendar list` checks only one calendar and can return `[]`; use the script above when Aki asks for incoming events.

## Three accounts, three config dirs

gws holds exactly one authenticated account per config directory, and the macOS keyring
entry it writes is service `gws-cli` / account `achibukz` — **not** namespaced per config
dir. So multi-account only works if each account uses its own config dir *and* the file
keyring backend. Both are env vars:

| Account | Purpose | Config dir |
|---|---|---|
| `aki.bukz12@gmail.com` | main email | `~/.config/gws-main` |
| `akibukuhan10@gmail.com` | sub-main email, school + personal calendar | `~/.config/gws-personal` |
| `akibukzwork@gmail.com` | work email, Job calendar | `~/.config/gws-work` |
| `abram_bukuhan@dlsu.edu.ph` | DLSU school mail (~12k msgs) + DLSU calendar | `~/.config/gws-dlsu` |

Every call needs both vars:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-work \
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
gws gmail users messages list --params '{"userId": "me", "q": "is:unread", "maxResults": 10}'
```

The bare `~/.config/gws` dir is the old single-account setup. Don't add to it.

## Re-authenticating (Run on Mac, then SCP to Linux)

When OAuth tokens expire, authenticate all 4 accounts on your Mac, then push the config directories to Achibuntu in one go:

### 1. Main Account (`aki.bukz12@gmail.com`)
```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-main \
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
gws auth login --services=gmail,calendar
```

### 2. Personal & School Calendar (`akibukuhan10@gmail.com`)
```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-personal \
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
gws auth login --services=gmail,calendar
```

### 3. Work & Job Calendar (`akibukzwork@gmail.com`)
```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-work \
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
gws auth login --services=gmail,calendar
```

### 4. DLSU School Mail (`abram_bukuhan@dlsu.edu.ph`)
```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-dlsu \
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
gws auth login --services=gmail,calendar
```

### 5. Push to Achibuntu
```bash
scp -r ~/.config/gws-* achibukz@achibuntu:~/.config/
```
worked, and both are now done:

1. **Consent screen published to Production.** In Testing, refresh tokens expire after 7
   days and non-test-users get `Error 403: access_denied`. Publishing removes both.
   Console → Google Auth Platform → Audience → Publish app.
2. **`roles/serviceusage.serviceUsageConsumer` granted** to `aki.bukz12@gmail.com`,
   `akibukuhan10@gmail.com`, and `abram_bukuhan@dlsu.edu.ph` on project `achiclaude`.
   Every account added later needs this too. Without it auth succeeds but every
   call returns *"Caller does not have required permission to use project achiclaude"* —
   gws sends a quota-project header that non-members may not use. Re-grant with:

   ```bash
   gcloud projects add-iam-policy-binding achiclaude \
     --member="user:<email>" --role="roles/serviceusage.serviceUsageConsumer" --condition=None
   ```

Health check all four at once:

```bash
for a in main personal work dlsu; do
  GOOGLE_WORKSPACE_CLI_CONFIG_DIR=$HOME/.config/gws-$a GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
    gws gmail users getProfile --params '{"userId": "me"}'
done
```

Check state: `gws auth status` with the same two env vars.

## Gmail

```bash
# list
gws gmail users messages list --params '{"userId": "me", "q": "from:recruiter after:2026/08/01", "maxResults": 20}'
# read one (metadata is enough for subject/from/date)
gws gmail users messages get --params '{"userId": "me", "id": "<msgId>", "format": "metadata"}'
# labels
gws gmail users labels list --params '{"userId": "me"}'
```

`q` takes normal Gmail search syntax. Message bodies come back base64url in
`payload.parts[].body.data`.

## Calendar

```bash
gws calendar calendarList list          # correct — "gws calendars list" is not a thing
gws calendar events list --params '{"calendarId": "primary", "timeMin": "2026-08-10T00:00:00+08:00", "timeMax": "2026-08-17T00:00:00+08:00", "singleEvents": true, "orderBy": "startTime"}'
```

With per-account config dirs, `"calendarId": "primary"` resolves to that account's own
calendar.

### Which account sees which calendar

**Use `gws-personal` for calendar by default.** It sees every school calendar plus the
personal ones, and it sees Job read-only. `gws-work` only matters for *writing* to Job.
`gws-main` holds almost nothing.

| Calendar | Access from personal | calendarId |
|---|---|---|
| Gala (akibukuhan10 primary) | owner | `akibukuhan10@gmail.com` (or `primary`) |
| Personal | owner | `e07625f82fb26f6efeb81b73f9f113004ecfb2bbd19cf14a87a0506af0e70163@group.calendar.google.com` |
| Bdayy | owner | `qu0a77mfnnvueucgcpk6jlbp9k@group.calendar.google.com` |
| DLSU | owner | `smm4dmf5g0j9lsjuq7pp2fk2ok@group.calendar.google.com` |
| THS-ST1 (thesis) | owner | `0f6d0da7524ad036d026ba445c0bad7036a911fb9b79fbd6930632ee067a61ea@group.calendar.google.com` |
| CSOPESY | owner | `1f26ef5f80172f4eb0cce714217c143395d2fdad98ef7b429b921d98a35e0f52@group.calendar.google.com` |
| STCLOUD | owner | `95eb55984b43edc63f3813771560ebc7a5889890142e5fd33e40c08f72c0c7d5@group.calendar.google.com` |
| STSP001 | owner | `07e0c241ce24356786e84efc570a0891c38aed9381481d285bb00477351d04e5@group.calendar.google.com` |
| PEDFOUR | owner | `1b246f66689aa177ce3c4339fb253ed160c4ae68be490969d53e87eaa1df8aae@group.calendar.google.com` |
| LSCS | owner | `0ad5a2c5ab6cfd9e35d9d2f39306654db9d6824b70a2d07f698d5201a0eee220@group.calendar.google.com` |
| Canvas import feed | **reader** | `ts4ja84d594ptjit87rv0bo63qilsjea@import.calendar.google.com` |
| DLSU account | freeBusy only | `abram_bukuhan@dlsu.edu.ph` |
| Job | **reader** | `akibukzwork@gmail.com` — to write, switch to `gws-work` |

Only under `gws-work`: Family (`family14882840659882912087@group.calendar.google.com`),
Holidays PH (`en.philippines#holiday@group.v.calendar.google.com`), and write access to Job.
Under `gws-main`: only aki.bukz12's own primary and Family. Nothing else lives there.

Under `gws-dlsu` (4 calendars): the DLSU primary `abram_bukuhan@dlsu.edu.ph` at **owner** —
`gws-personal` only sees this one as `freeBusyReader`, so use `gws-dlsu` when event *details*
matter. Plus `DLSU ALTDSI`
(`dlsu.edu.ph_jr27vbd0426ik7pg7ctpncg4qg@group.calendar.google.com`, reader), the Canvas
feed, and Holidays PH.

Canvas already pushes DLSU deadlines into that import feed, so course due dates are
readable via `gws` without touching Chrome. It is read-only and Canvas-controlled — never
try to write to it, and treat `/canvas-tracker` as authoritative when the two disagree.

Creating events: always bake in a 15-minute popup reminder (standing rule).

```bash
gws calendar events insert --params '{"calendarId": "primary"}' --json '{
  "summary": "...",
  "start": {"dateTime": "2026-08-12T16:00:00+08:00", "timeZone": "Asia/Manila"},
  "end":   {"dateTime": "2026-08-12T16:45:00+08:00", "timeZone": "Asia/Manila"},
  "reminders": {"useDefault": false, "overrides": [{"method": "popup", "minutes": 15}]}
}'
```

Recurrence goes in `"recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=TU;UNTIL=20260814T155959Z"]`.

## Parsing output from Python

gws prints a keyring banner before the JSON and appends trailing data after it, so
`json.loads` raises `Extra data`. Use `raw_decode`, one `subprocess.run` per call.

```python
import subprocess, json, os

env = {**os.environ,
       "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": os.path.expanduser("~/.config/gws-work"),
       "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND": "file"}
r = subprocess.run(["gws", "gmail", "users", "messages", "list",
                    "--params", json.dumps({"userId": "me", "maxResults": 10})],
                   capture_output=True, text=True, env=env)
raw = r.stdout + r.stderr
obj, _ = json.JSONDecoder().raw_decode(raw[raw.find("{"):])
```

## Common mistakes

| Wrong | Right |
|---|---|
| `gws calendars list` | `gws calendar calendarList list` |
| calling gws with no config-dir env var | always set `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` — the default dir is the stale single-account one |
| setting config dir but not `KEYRING_BACKEND=file` | both, or accounts overwrite each other in the macOS keyring |
| `json.loads(raw)` | `json.JSONDecoder().raw_decode(raw[raw.find("{"):])` |
| separate patch call to add reminders | put `reminders` in the insert body |
