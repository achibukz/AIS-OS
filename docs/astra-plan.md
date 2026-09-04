# Astra Audit and Leverage Plan

Audit and review plan for achiOS, achiCore, achiMem, and active agent sessions upon Project Astra release.

## 1. Review How You Work

Provide Astra your session and project history across Claude, Codex, Hermes, and any other agent you use.

Ask it to find:
- Prompts you repeat across sessions
- Manual steps that should become scripts or integrations
- Repeatable workflows that should become skills
- Corrections that belong in project instructions
- Scheduled work that should become cron jobs
- Files or steps where sessions repeatedly stop

## 2. Audit Your Second Brain

Inspect how knowledge enters, gets structured, becomes searchable, and gets used by your agents across vaults (`achiMem`, `schoolMem`).

Review targets:
- Folder structure and data schemas
- Duplicate or conflicting knowledge
- Retrieval gaps
- Cron jobs and ingestion workflows
- How sessions and research get saved
- Files and data that you and your agents never use

## 3. Review Your Evergreen Projects

Send Astra your most important projects across achiOS, achiCore, and personal tooling, especially the ones earlier models could not get working properly.

Execution protocol:
- Inspect project files, run existing tests, and trace failed workflows.
- Write a prioritized plan with the files to change and the checks each change must pass.
- Write every approved improvement back into the project, skill library, or company brain.
- Use Astra for planning and review, then hand the defined execution plan to cheaper models.
