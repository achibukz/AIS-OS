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

    rendered = task_engine.render_tasks(task_engine.parse_tasks(body), today=TODAY)

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
    assert "school, projects, personal, career, systems, uncategorized" in message


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
