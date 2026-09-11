"""Parse and render the achiOS Markdown task register."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from zoneinfo import ZoneInfo

PRIMARY_AREAS = ("school", "projects", "personal", "career", "systems")
FILTER_AREAS = (*PRIMARY_AREAS, "uncategorized")

TASK_RE = re.compile(r"^\s*-\s*\[([ x~])\]\s+(.*\S)\s*$")
DUE_RE = re.compile(r"@(\d{4}-\d{2}-\d{2})")
PRIORITY_RE = re.compile(r"!(high|med|low)\b", re.IGNORECASE)
TAG_RE = re.compile(r"(?<!\S)#([A-Za-z][\w-]*)")
TASK_ID_RE = re.compile(r"\s*<!--\s*task-id:\s*([A-Za-z0-9][A-Za-z0-9._:-]*)\s*-->")
FENCE_RE = re.compile(r"^\s*```")
WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[([^\[\]]+)\]\([^\)]+\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")

PRIORITY_ORDER = {"high": 0, "med": 1, "low": 2}
LOCAL_TZ = ZoneInfo("Asia/Manila")


@dataclass(frozen=True)
class Task:
    text: str
    state: str
    priority: str = "med"
    due: dt.date | None = None
    area: str | None = None
    tags: tuple[str, ...] = ()
    task_id: str | None = None


def strip_markup(text: str) -> str:
    text = WIKI_LINK_RE.sub(r"\1", text)
    text = MARKDOWN_LINK_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = CODE_RE.sub(r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_tasks(body: str) -> list[Task]:
    """Return every active and blocked task from Markdown register content."""
    tasks: list[Task] = []
    current_section = ""
    in_fence = False

    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            continue
        if current_section not in {"active", "active tasks", "blocked", "blocked tasks"}:
            continue

        match = TASK_RE.match(line)
        if not match:
            continue
        marker, raw = match.groups()
        if marker == "x":
            continue

        task_id_match = TASK_ID_RE.search(raw)
        raw_without_id = TASK_ID_RE.sub("", raw)
        due_match = DUE_RE.search(raw_without_id)
        priority_match = PRIORITY_RE.search(raw_without_id)
        tags = tuple(TAG_RE.findall(raw_without_id))
        primary_matches = tuple(
            dict.fromkeys(tag.lower() for tag in tags if tag.lower() in PRIMARY_AREAS)
        )
        area = primary_matches[0] if len(primary_matches) == 1 else None
        remaining_tags = tuple(tag for tag in tags if tag.lower() not in PRIMARY_AREAS)
        text = TAG_RE.sub(
            "",
            PRIORITY_RE.sub("", DUE_RE.sub("", raw_without_id)),
        )

        tasks.append(
            Task(
                text=strip_markup(text),
                state="blocked" if marker == "~" or current_section.startswith("blocked") else "active",
                priority=priority_match.group(1).lower() if priority_match else "med",
                due=dt.date.fromisoformat(due_match.group(1)) if due_match else None,
                area=area,
                tags=remaining_tags,
                task_id=task_id_match.group(1) if task_id_match else None,
            )
        )

    seen_ids: set[str] = set()
    for task in tasks:
        if task.task_id is None:
            continue
        if task.task_id in seen_ids:
            raise ValueError(f"duplicate task ID: {task.task_id}")
        seen_ids.add(task.task_id)
    return tasks


def _sort_key(task: Task) -> tuple[dt.date, int, str]:
    return task.due or dt.date.max, PRIORITY_ORDER[task.priority], task.text.casefold()


def _format_task(task: Task) -> str:
    metadata = [f"!{task.priority}"]
    if task.due:
        metadata.append(f"@{task.due.isoformat()}")
    metadata.extend(f"#{tag}" for tag in task.tags)
    marker = "☒" if task.state == "blocked" else "☐"
    return f"• {marker} {task.text} ({', '.join(metadata)})"


def render_tasks(
    tasks: list[Task],
    *,
    area: str | None = None,
    today: dt.date | None = None,
) -> str:
    """Render a deterministic, lossless active-task view."""
    if area is not None and area not in FILTER_AREAS:
        choices = ", ".join(FILTER_AREAS)
        raise ValueError(f"unknown area {area!r}; valid choices: {choices}")

    today = today or dt.datetime.now(LOCAL_TZ).date()
    selected = [
        task
        for task in tasks
        if area is None
        or task.area == area
        or (area == "uncategorized" and task.area is None)
    ]
    lines = ["TASKS", f"As of {today.isoformat()}", ""]

    active = [task for task in selected if task.state == "active"]
    blocked = [task for task in selected if task.state == "blocked"]
    dated = [task for task in active if task.due is not None]
    deadline_groups = (
        ("OVERDUE", [task for task in dated if task.due < today]),
        ("DUE TODAY", [task for task in dated if task.due == today]),
        ("UPCOMING", [task for task in dated if task.due > today]),
    )
    for heading, group in deadline_groups:
        if group:
            lines.append(heading)
            lines.extend(_format_task(task) for task in sorted(group, key=_sort_key))
            lines.append("")

    undated = [task for task in active if task.due is None]
    area_order = FILTER_AREAS if area is None else (area,)
    for area_name in area_order:
        group = [
            task
            for task in undated
            if task.area == area_name or (area_name == "uncategorized" and task.area is None)
        ]
        if group:
            lines.append(area_name.upper())
            lines.extend(_format_task(task) for task in sorted(group, key=_sort_key))
            lines.append("")

    if blocked:
        lines.append("BLOCKED")
        lines.extend(_format_task(task) for task in sorted(blocked, key=_sort_key))
        lines.append("")

    count = len(selected)
    if count == 0:
        lines.extend(["No active or blocked tasks.", ""])
    noun = "task" if count == 1 else "tasks"
    lines.append(f"{count} {noun}")
    return "\n".join(lines).strip()
