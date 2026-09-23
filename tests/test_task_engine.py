import datetime as dt

import pytest
import task_engine

TODAY = dt.date(2026, 9, 11)


def test_parser_retains_state_metadata_tags_and_stable_ids():
    body = """## Active
- [ ] Ship parser #systems #achicore #THS-ST2 !high @2027-02-01 <!-- task-id: task-123 -->
- [~] Waiting for access #career #github !low
"""

    tasks = task_engine.parse_tasks(body)

    assert tasks == [
        task_engine.Task(
            text="Ship parser",
            state="active",
            priority="high",
            due=dt.date(2027, 2, 1),
            area="systems",
            tags=("achicore", "THS-ST2"),
            task_id="task-123",
        ),
        task_engine.Task(
            text="Waiting for access",
            state="blocked",
            priority="low",
            area="career",
            tags=("github",),
        ),
    ]


@pytest.mark.parametrize("area", task_engine.PRIMARY_AREAS)
def test_each_primary_area_filter_returns_only_that_area(area):
    body = "\n".join(
        ["## Active"]
        + [f"- [ ] {candidate} task #{candidate}" for candidate in task_engine.PRIMARY_AREAS]
    )

    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), area=area, today=TODAY)

    assert f"{area} task" in rendered
    for other in set(task_engine.PRIMARY_AREAS) - {area}:
        assert f"{other} task" not in rendered
    assert "1 task" in rendered


def test_uncategorized_view_keeps_missing_invalid_and_ambiguous_areas_visible():
    body = """## Active
- [ ] Missing area !high
- [ ] Invalid area #misc
- [ ] Ambiguous area #school #career
"""

    rendered = task_engine.render_tasks(
        task_engine.parse_tasks(body), area="uncategorized", today=TODAY
    )

    assert "Missing area" in rendered
    assert "Invalid area" in rendered
    assert "Ambiguous area" in rendered
    assert "3 tasks" in rendered


def test_full_view_is_lossless_and_orders_deadlines_before_blocked_tasks():
    body = """## Active
- [ ] Far future #projects !med @2028-12-31
- [ ] Dated high #personal !high @2026-12-01
- [ ] Undated #school !low
- [~] Blocked item #systems !high @2026-09-01
"""

    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), area="all", today=TODAY)

    for title in ("Far future", "Dated high", "Undated", "Blocked item"):
        assert rendered.count(title) == 1
    assert rendered.index("Dated high") < rendered.index("Undated")
    assert rendered.index("Far future") < rendered.index("Undated")
    assert rendered.index("Undated") < rendered.index("Blocked item")
    assert "@2028-12-31" in rendered
    assert "!high" in rendered
    assert "4 tasks" in rendered
    assert sum(line.startswith("• ") for line in rendered.splitlines()) == 4
    assert "task-" not in rendered


def test_unknown_filter_lists_the_valid_choices():
    with pytest.raises(ValueError) as exc_info:
        task_engine.render_tasks([], area="finance", today=TODAY)

    message = str(exc_info.value)
    assert "school, projects, personal, career, systems, uncategorized, all, backlog" in message
    assert "backlog" in message
    assert "all" in message


def test_empty_register_has_an_explicit_zero_count():
    rendered = task_engine.render_tasks([], today=TODAY)

    assert "No active or blocked tasks." in rendered
    assert "0 tasks" in rendered


def test_parser_ignores_examples_and_completed_tasks():
    body = """## Active
```
- [ ] Example #school
```
- [ ] Real #personal

## Done
- [x] Finished #projects
"""

    assert [task.text for task in task_engine.parse_tasks(body)] == ["Real"]


def test_issue_links_are_text_not_area_tags():
    body = (
        "## Active\n"
        "- [ ] Fix [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) "
        "#systems #bug\n"
    )

    assert task_engine.parse_tasks(body) == [
        task_engine.Task(
            text="Fix AIS-OS #34",
            state="active",
            area="systems",
            tags=("bug",),
        )
    ]


def test_duplicate_stable_ids_are_rejected():
    body = """## Active
- [ ] First #systems <!-- task-id: repeated -->
- [ ] Second #projects <!-- task-id: repeated -->
"""

    with pytest.raises(ValueError, match="duplicate task ID: repeated"):
        task_engine.parse_tasks(body)


def test_default_view_excludes_systems_tasks():
    body = """## Active
- [ ] Cancel Google One #personal !low @2026-10-13
- [ ] Fix message splitting through [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) #systems #bug !med
- [ ] Filter /tasks views [AIS-OS #55](https://github.com/achibukz/AIS-OS/issues/55) #systems !high
"""
    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), today=TODAY)
    assert "Cancel Google One" in rendered
    assert "Fix message splitting" not in rendered
    assert "Filter /tasks views" not in rendered


def test_default_view_excludes_bare_ticket_references():
    body = """## Active
- [ ] Deliver approved Telegram cohesion batch achiCore #194-#200 and AIS-OS #41-#49 #systems !high
- [ ] Forward args natively in achiCore #57 #career !med
"""
    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), today=TODAY)
    assert "Deliver approved" not in rendered
    assert "Forward args" not in rendered


def test_default_view_excludes_non_school_research_keeps_school_research():
    body = """## Active
- [ ] Research model selection guide #achios #reference #research !med
- [ ] Research thesis methodology chapter #school #research !high
"""
    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), today=TODAY)
    assert "model selection" not in rendered
    assert "thesis methodology" in rendered


def test_area_all_includes_everything_except_backlog():
    body = """## Active
- [ ] Personal task #personal !med
- [ ] Systems ticket [AIS-OS #55](url) #systems !high
- [ ] Research tooling #achios #research !med
## Backlog
- [ ] Deferred work #projects !low
"""
    tasks = task_engine.parse_tasks(body)
    rendered = task_engine.render_tasks(tasks, area="all", today=TODAY)
    assert "Personal task" in rendered
    assert "Systems ticket" in rendered
    assert "Research tooling" in rendered
    assert "Deferred work" not in rendered


def test_backlog_parsing_and_area_backlog():
    body = """## Active
- [ ] Active work #personal !high
## Backlog
- [ ] Backlogged item #projects !low
- [x] Done backlog #school
- [~] Blocked backlog #career !med
"""
    tasks = task_engine.parse_tasks(body)
    backlog = [t for t in tasks if t.state == "backlog"]
    assert len(backlog) == 2
    assert backlog[0].text == "Backlogged item"

    rendered = task_engine.render_tasks(tasks, area="backlog", today=TODAY)
    assert "Backlogged item" in rendered
    assert "Blocked backlog" in rendered
    assert "Active work" not in rendered


def test_backlog_never_appears_in_default_or_primary_area_views():
    body = """## Active
- [ ] School work #school !med
## Backlog
- [ ] Backlogged school item #school !high
"""
    tasks = task_engine.parse_tasks(body)
    for area in [None, "school", "all"]:
        rendered = task_engine.render_tasks(tasks, area=area, today=TODAY)
        assert "Backlogged school item" not in rendered


def test_backlogs_alias_accepted():
    body = """## Backlog\n- [ ] Deferred #projects !low\n"""
    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), area="backlogs", today=TODAY)
    assert "Deferred" in rendered


def test_invalid_area_lists_all_valid_choices():
    with pytest.raises(ValueError, match="all") as exc_info:
        task_engine.render_tasks([], area="finance", today=TODAY)
    msg = str(exc_info.value)
    assert "backlog" in msg
    assert "all" in msg


def test_explicit_area_systems_shows_ticket_linked_systems_tasks():
    body = """## Active
- [ ] Fix splitting [AIS-OS #34](url) #systems #bug !med
- [ ] Personal errand #personal !low
"""
    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), area="systems", today=TODAY)
    assert "Fix splitting" in rendered
    assert "Personal errand" not in rendered


def test_task_retains_raw_text():
    body = """## Active
- [ ] Fix message splitting through [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) #systems #bug !med
"""
    tasks = task_engine.parse_tasks(body)
    assert len(tasks) == 1
    assert (
        tasks[0].raw_text
        == "Fix message splitting through [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) #systems #bug !med"
    )
