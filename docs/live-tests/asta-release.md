# Asta release acceptance

Status: not run. Record the AIS-OS and companion achiCore head SHAs before testing.
A changed head invalidates earlier observations. Keep private outputs outside Git.

AIS-OS head:
achiCore head:
Actual engine, model and effort:
Tester and date:

Use isolated database, photo storage and a test workout calendar first. Set
`ACHIOS_HOME` to the staging operator root and use a staged persona with the CLI
path pointing to this checkout. Do not replace production bindings. Configure a
separate test bot, chat and Asta binding for summary delivery. Stop on a destination
mismatch, invented success or loss of the original estimate.

| Action | Expected | Actual |
|---|---|---|
| Run `asta.py status` | Schema 1, missing profile fields, no invented targets | |
| Import an explicitly reviewed onboarding JSON through `profile set --json -` | Versioned profile; skipped fields remain missing | |
| Run `targets suggest`, then approve or override through `targets set` | Values match the tool; provenance records the choice | |
| Search three Filipino dishes and one generic food | Sources are named; missing seed or USDA key produces a warning | |
| Tell Asta a clear text meal | Stored totals come from grams and food records | |
| Send a food photo with enough information | Range and confidence in reply; retained image and source removed | |
| Send an ambiguous photo | One focused question; no meal saved; attachment remains | |
| Correct a meal and inspect it | Current totals change; original estimate and reason remain | |
| Run `/mealcheck`, correct a flagged meal, run it again | List reflects the saved tier | |
| Ask for this week's school and work schedule | Asta calls `gcal.py agenda` itself | |
| Request one session on the test calendar | One event with `achios_owner=asta` and stable item ID | |
| Request a week plan, then cancel | Confirmation before any calendar writes | |
| Preview and trigger the daily service in isolation | Correct Asta thread, totals and sessions; no fabricated intake | |
| Run the backup service and restore its file to a temporary database | Integrity check passes and records match | |

After accepted staging, explicitly approve production deployment. Confirm the
production binding and hub bot identity, import only reviewed private onboarding
values, provision private config, then enable the two timers. Record actual timer
state and first backup. Apple Health is not part of this release.

Cleanup removes only recorded staging artifacts. Keep production databases and
retained photos. Disable staging timers and restore any recorded staging
configuration. A pass means ready for the user's merge decision, not merged.
