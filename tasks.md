# Tasks

Aki's master task register. achiOS hosts this — settled 2026-08-10 (see
`achiMem/wiki/personal/open-questions.md`). Tasks are operating state; achiMem records
knowledge, not pending work.

Read by `scripts/daily_brief.py` for the 8am Telegram brief. Keep the line format below or
the parser skips the line.

## Format

```
- [ ] What to do #area !high @2026-08-20
```

- `- [ ]` active, `- [x]` done, `- [~]` blocked
- `#area` optional, one or more. Free-form: `#thesis`, `#career`, `#achios`, `#school`
- `!high` `!med` `!low` optional. Missing means `!med`
- `@YYYY-MM-DD` optional due date. Overdue and due-today are called out in the brief

Move finished items to `## Done` with the completion date appended. Don't delete them.

## Active

- [ ] Set achibuntu BIOS to power on after AC loss — F10 at boot, it is batteryless so a mains blip kills it #infra !med
- [ ] Confirm which ING team Aki is joining — Data/AI/Transformation vs Retail Tech, one message to Vanscell Nierra #career !high
- [ ] Approach the DLSU school coordinator for the internship agreement signature #career !high
- [ ] Fix `career-ops/config/profile.yml` — still says T1 starts 2026-08-03, feeds wrong availability into live applications #career !high
- [ ] Add the oboda row to `career-ops/data/applications.md` — offer received and declined, missing entirely from the tracker #career !med
- [ ] Mount the 1 TB HDD at `/srv` and set up restic or borg backups for both vaults #achios !med
- [ ] Run `ADD TERM` for `AY2627-T1` in schoolMem once enlistment lands #school !low @2026-09-03
- [ ] Fix stale skill descriptions — `thesis-script-writer` and `thesis-humanizer` reference C3-LMM and MicroTok-PH, which match neither vault #achios !low

## Blocked

- [~] Pull the power cord on achibuntu to test unattended boot recovery — BIOS has no "Restore on AC Power Loss", depends on a ten-year-old battery #achios !med

## Done
