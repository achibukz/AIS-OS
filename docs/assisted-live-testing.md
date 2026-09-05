# Assisted feature live testing

Use the `assisted-live-testing` skill when a feature needs a human action or observation to establish acceptance. This includes a backend CLI, API credentials, an external event, a device, a browser or Telegram. Automated-only tickets keep their existing test workflow. A design decision is still a discussion, not a live test.

The assistant prepares the environment, explains one action at a time, waits for the result, verifies available evidence and keeps a resume checkpoint. The outputs are a redacted Markdown interaction record and a comment on the tested PR. Source: [skill](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/SKILL.md), [ticket section](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/assets/ticket-section.md), [run record](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/assets/run-record.md).

## Call it

Select the assistant model in the client first. Then send:

> Use assisted-live-testing for PR <URL> at <SHA>. Test <criteria> in <environment>. Prepare what you can and guide me one action at a time through the steps that need me. Explain any CLI command and where to run it. Verify the results against logs or state. Save a redacted Markdown record of our interaction and receipts, and post a comment on the PR. Use gemini-3.8-flash-high for product turns if the feature supports it; report any required engine coverage we do not exercise.

A skill does not change the assistant model. The product under test can use a different model. A feature requiring Codex or Claude Code still needs that engine even if the assisting session runs on Flash.

A bound achiCore topic must include this skill in its persona allowlist before the prompt index or scoped engine home advertises it. Installing the skill globally does not change production personas. In an already-open client, start a fresh session if discovery has not refreshed, or ask it to read the installed SKILL.md directly.

## Reuse the Telegram hub

Testing Grounds already exists. Read [the hub reference](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/references/telegram-hub.md) before changing its candidate or starting a test. It records the operator-config path, owned root, console and log commands, identity checks, model setup, graceful stop and restart. The config holds secrets and stays outside the repository. The current run's existence does not establish readiness for a new candidate.

## Write a ticket that someone can test

Separate implementation from assisted feature live testing. Name the environment owner, prerequisites, exact human actions, expected results, observation tools, models, allowed side effects and outputs. Include the [copyable ticket section](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/assets/ticket-section.md) only when applicable. Fill in the PR and head at handoff; an issue number alone is not a candidate revision.

For the learning loop, build replay fixtures while T1 is implemented. T9's real Flash pilot can use this skill once its dependencies are ready. Telegram isolation alone does not isolate Calendar, task files, SQLite or vault writes. Those destinations need their own test ownership and cleanup receipts.

## Skill or agent

Start with a skill in the existing conversation. It works with different models and needs no extra bot identity or permanent process. Consider a dedicated assistant only when there is a concrete need for its own queue, persistent scheduling or access policy. The saved run record supplies continuity between sessions today.

Source review: [AIS-OS PR #21](https://github.com/achibukz/AIS-OS/pull/21), tracked by issue #20. The skill is installed locally; this PR is not merged.
