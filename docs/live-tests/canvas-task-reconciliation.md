# Canvas task reconciliation live test

Run this checklist against an isolated Canvas cache, cohesion database, task
file and test calendar before enabling a production course.

## Setup

- Copy the current Canvas database and `tasks.md` into the staging directory.
- Point the cohesion writer at the copied task file, a new database and a test
  calendar config.
- Record the branch head and the output of the repository test command.
- Choose one mapped current-term course with one unfinished assignment.

## Cases

1. Run `canvas.py tasks-preview --course <code>`. Record the eligible,
   blocked and announcement-task counts. Confirm the preview changes no file.
2. Run `canvas.py tasks-activate --course <code>` once. Confirm it reports the
   queued count. Run it again and confirm `activated` is false with no duplicate
   operation.
3. Run `canvas.py tasks-reconcile`. Confirm the JSON names task-applied and
   Calendar-applied counts separately. Inspect the copied task file and test
   calendar for one linked item.
4. Replay the same Canvas snapshot and retry reconciliation. Confirm there is
   still one task and one Calendar event.
5. Change the assignment title and due date, then restore the original due
   date. Confirm every transition updates the same task and event identity.
6. Change the submission state to submitted, graded, completed and excused in
   separate fixture runs. Confirm the stored source state remains distinct and
   the linked task completes once. Use an unknown state and confirm it stays a
   conflict without changing either destination.
7. Add a high-confidence announcement such as "Submit Homework 2 by September
   30". Confirm one announcement task appears. Remove the explicit date or the
   action phrase and confirm no task operation appears.
8. Put a matching imported event on the test calendar. Confirm the Calendar
   operation stays pending, the imported event is unchanged and the task result
   is reported independently.
9. Deliver the Canvas notification before task reconciliation. Confirm the
   notice becomes sent while the task operation remains pending.
10. Mark assignment coverage stale or failed. Confirm activation refuses it and
    no destination changes.

## Actual results

- Branch head:
- Automated tests:
- Preview counts:
- Task result:
- Calendar result:
- Announcement extraction:
- Imported-event result:
- Notification independence:
- Pass, fail or skip:
