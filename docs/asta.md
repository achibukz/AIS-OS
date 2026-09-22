# Asta tracking

Asta stores profile versions, targets, meal estimates and corrections in a private
SQLite database. The CLI calculates nutrients from grams and food records. The
model supplies portions and uncertainty, then reports the CLI result.

This release covers AIS-OS #63 through #68. The companion achiCore change updates
the Calendar instructions and adds `/mealcheck`. Apple Health and the later
nutrition and lifting integrations remain separate work.

## Install and paths

The existing achiOS interpreter needs `requests` and `Pillow`. Provision missing
packages with `uv pip install --python ~/.local/share/achios/venv/bin/python requests Pillow`.
The repository test suite also requires pytest.

Run `~/.local/share/achios/venv/bin/python scripts/asta.py status` to initialize.
`ACHIOS_HOME` overrides the operator home for staging. `--db PATH` overrides only
the database; use `ACHIOS_HOME` too when isolating photos, credentials and config.
The CLI finds the operator home from the checkout under `Code/GitHub` when a
bound agent has a scoped HOME.

| Data | Default location under the operator home |
|---|---|
| Database | `.local/state/achios/asta/asta.sqlite3` |
| Private PhilFCT seed | `.local/state/achios/asta/staples.json` |
| USDA API key, plain text | `.config/achios/asta/usda.key` |
| Threshold overrides | `.config/achios/asta/config.json` |
| Summary delivery config | `.config/achios/asta/delivery.json` |
| Retained meal images | `Documents/Files/training/asta/meals/YYYY/MM/` |
| Nightly backups | `Documents/Files/training/asta/backups/` |

No onboarding answers, food photographs, PhilFCT values or credentials belong in
this repository. Read commands do not initialize a missing database. Existing
records remain readable while another connection holds a reserved write lock.

## Profile, targets and weight

`profile set --json -` accepts a partial JSON object on stdin and appends a
version. `profile show` reports missing target inputs. Field names and accepted
values are documented in the Asta persona in achiCore. A skipped field may be
null. The onboarding draft can be imported through these fields without copying
private content into source control.

`targets suggest` uses the current profile and saves nothing. It returns missing
inputs instead of guessing an activity factor or goal. `targets set --json -`
accepts `kcal`, `protein`, `carbs` and `fat`, each shaped as
`{"value": 123, "source": "overridden"}`. Use `computed` only for an unchanged
value from the current suggestion. Targets keep the profile version they used.

`weight add KG --date YYYY-MM-DD` replaces that day's weight. `weight trend`
returns recent entries and the average of recorded days within the last seven
calendar days in Manila. It does not fill gaps or include future entries.

## Food and meals

`food search "query"` returns personal templates, matching private staples, then
USDA results. The USDA cache lasts seven days. Missing credentials and network
failures return local results with a warning. Missing USDA nutrients do not
become zeros. The transport follows the [USDA API guide](https://fdc.nal.usda.gov/api-guide/).

The seed is a JSON array. Each record has `id: "philfct:CODE"`, `source:
"philfct"`, `source_id: "CODE"`, `label`, `copied_at` as an ISO date, and
`per_100g` containing `kcal`, `protein`, `carbs` and `fat`. Malformed rows produce
a warning while valid rows remain available. The committed example is empty.

`meal add --json -` takes the persona's meal contract. It rejects caller totals
and unknown foods. Each saved item keeps its nutrient source and nutrient values
used in the calculation. Density estimates always flag, including when reused
through a saved template. The configured thresholds choose `committed`, `flagged`
or `needs_answer`. A question writes no meal and leaves its attachment intact.

`meal correct ID --json -` accepts the complete corrected `items` array and a
`reason`. Corrections append old and new values; `meal show ID` returns both the
original estimate and the current meal. `meal delete ID` deletes the meal and
its correction rows. Retained media stays on disk under the agreed indefinite
retention policy.

`template save --from-meal ID --name NAME` stores a reusable food record from
confirmed portions. It refuses uncertain gram ranges and preserves estimated
nutrient provenance. `template search "query"` reads saved templates.

Photo meals accept JPEG, PNG and WebP files beneath the hub attachment root.
The CLI rejects symlinks, outside paths and invalid images. Successful storage
retains one file per content hash and removes the attachment after the meal
commit. If cleanup fails, the result says `attachment_cleanup_pending`. A crash
between file retention and the database commit can leave a retained file; a
retry recognizes its content hash. Reusing a photo links the same image but is
still a new meal operation.

## Daily summaries and backups

`today --date YYYY-MM-DD` returns logged nutrients, targets, flagged count,
weight average and sessions from the workouts Calendar. Missing meals mean
unknown intake. Calendar failure leaves nutrition available with a warning.
`adherence set --event ID done|skipped|moved` records the user's report.

`asta_daily.py --dry-run` previews the deterministic summary. Delivery requires
private JSON with `env_path` and a positive `thread_id`. The env file must contain
both `TELEGRAM_BOT_TOKEN` for the hub bot and `TELEGRAM_CHAT_ID`. The script checks
that the configured chat and thread currently bind to `asta` in the hub's
`topics.json` before sending. Verify the bot identity during live setup.

The daily timer runs at 21:00 Manila. The backup timer runs at 02:30 Manila and
keeps the newest 14 verified SQLite backups. A failed backup does not prune old
copies. The backup process owns its target directory and resets its mode to `0700`
before every run. A mode such as `0500` on that owned directory is repaired, while
an actual file-creation failure aborts the run and preserves existing backups.
Both use the existing service failure alert. Unit files are supplied but
are not enabled by this change. Provision the database and delivery config before
installing the timers through the existing unit installer. That installer affects
all repository timers, so inspect the deployment first.

## Verification

Run `~/.local/share/achios/venv/bin/python -m pytest tests -q` from this checkout.
Tests use temporary databases and fake USDA, Calendar and Telegram transports.
The [live checklist](live-tests/asta-release.md) records the separate phone and
timer acceptance. Automated tests do not establish deployment or coach quality.
