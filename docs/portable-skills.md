# achiOS access across clients and repositories

Four skills let Codex CLI, Codex desktop, Claude Code and Antigravity use existing
achiOS services while the working directory is another repo. Code and skills live
in this checkout. OAuth credentials, Calendar ownership, Canvas state and vaults
stay outside Git.

The [portable agent pack](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/portable-agents.md)
adds the Telegram personas as globally available Codex and Claude Code agents.

## Install on the Mac or server

Pull achiOS first, then run the installer with Python 3.11 or newer:

```bash
cd ~/Code/GitHub/AIS-OS
git pull --ff-only
python3 scripts/install_portable_skills.py --dry-run
python3 scripts/install_portable_skills.py
python3 scripts/achios_workspace.py doctor
```

If macOS's `python3` is older, use `uv run --python 3.11` in place of `python3`.
The Google helper and installer use only the standard library. Calendar and Canvas
use the existing service dependencies; use the achiOS environment that already
runs those scripts, or `uv run --python 3.11 --with requests --with PyYAML`.

The default installer links only these four skills into the user directories
`~/.agents/skills` for Codex and `~/.claude/skills` for Claude Code. Those skills
are available across repos. It preflights conflicts and leaves existing skills
intact. It does not edit credentials, client settings, hooks or other skills.
Restart the CLI session or open a new desktop chat to check discovery. Skill
selection depends on the client's model; explicit invocation is available too.

[Codex's skill documentation](https://developers.openai.com/codex/skills/) describes
user discovery and symlink support. [Claude Code's skill documentation](https://code.claude.com/docs/en/skills)
describes personal skills and automatic selection.

For a Skillshare-managed machine, install into its source instead and run its
normal sync, so Skillshare owns the client links:

```bash
python3 scripts/install_portable_skills.py --target skillshare
skillshare sync
```

Antigravity can use `--target agy`. Hub personas still need these skill names in
their allowlists. This change does not broaden those allowlists or restart the hub.

## Existing Google accounts

The supported aliases are `main`, `personal`, `work` and `dlsu`, using the existing
`~/.config/gws-<alias>` directories. Aki already has the original credentials on
the Mac. Reuse them. `doctor` checks token state and lists scopes without printing
tokens. It does not log in or prove access to every file.

The helper finds gws on PATH, including a Homebrew or npm installation. Set
`ACHIOS_GWS_BIN` if the desktop client's PATH omits it. Set `ACHIOS_HOME` to the
credential home when using a checkout outside `~/Code/GitHub`, or a scoped home
whose checkout is elsewhere. The helper overrides inherited account token/file
environment variables for each named profile, using the file keyring backend these profiles were created with unless an
explicit backend is already configured. It does not copy profiles between machines.

Example from schoolMem:

```text
Use achios-google to read this Google Docs link with my DLSU account: <link>
```

The agent checks `dlsu`, resolves the Docs ID and calls the API with all tabs
included. The helper also searches Gmail, reads messages and searches Drive.
Its `exec` command runs other installed gws JSON operations under the selected
profile, including schema inspection and authorized edits. Calendar mutations
retain achiOS's writer ownership rules.

Missing profiles, missing gws, authentication failure and file access refusal are
separate outcomes. Existing credentials can lack scopes or permission to a file.
A failure does not authorize trying other identities or starting OAuth again.
The installed [Google Workspace CLI](https://github.com/googleworkspace/cli) remains
the Google API client.

## Other Telegram capabilities

| Skill | Shared behavior | Limit |
|---|---|---|
| achios-planning | Shared task register and Calendar reads; guidance for authorized linked changes through cohesion | Tasks reflect this checkout. Calendar needs its private config. Writer ownership remains enforced. |
| achios-canvas | Cached courses, deadlines, grades and announcements with freshness reporting | The Mac reads the existing server cache over its verified SSH connection when no local cache exists. Refresh and login stay with the coordinator. |
| achios-recall | Recent achiMem sessions and source-based vault searches | Local files must exist. This does not transfer chat history or install the learning loop. |

Useful later ports are document-store retrieval and media delivery, on-demand brief
previews, authorized reminder management, and hub job status. They need separate
contracts for their destination, state owner and evidence of completion. Model
selection, topic bindings and active-session cancellation remain client or hub
controls. A skill should not emulate those by editing runtime JSON.

## Verify after installation

From schoolMem or another repo, start a new client session and try these requests:

```text
Use achios-google to check my DLSU connection, then read <an existing Docs link>.
Use achios-planning to show all my school tasks and tomorrow's Calendar.
Use achios-canvas to show upcoming assignments and the cache timestamp.
Use achios-recall to find the source for my last thesis decision.
```

A real document read verifies Google access. Token status alone does not. A missing
Canvas cache or unsynced vault should produce a stated limitation. Automated tests
cover account isolation, symlink discovery, execution from another repo, installer
conflicts and read-only service routing. They do not prove model selection or Mac
access until those checks run there.

## Installation evidence, October 1, 2026

The skills are installed on achibuntu and AchiBook Air. The Mac's achiOS checkout
fast-forwarded without changing its local `projects/scribe/.gitignore` edit. Its
existing four OAuth profiles authenticated and completed Gmail profile and Drive
list reads. A DLSU Doc read returned all three tabs. No OAuth login was required.

Calendar reads succeeded after copying the server's private calendar mapping to
`~/.config/achios/calendars.json` on the Mac with mode 600. Tasks and recent session
recall ran from the schoolMem working directory. Canvas reads succeeded through
Mac-to-server SSH. Its September 28 cache reports stale data; no refresh or
notification was triggered. Model selection inside a new desktop or CLI chat has
not been exercised by these command checks.

Final automated checks passed with 923 tests on the server and 30 portable-skill
tests on the Mac. One existing server warning concerns an unregistered pytest
marker. The Mac Calendar read also passed without a login shell.
