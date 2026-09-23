#!/usr/bin/env python3
"""Read the active schoolWiki term and subjects without changing the vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _wiki_file(wiki: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe wiki path: {relative}")
    resolved = (wiki / path).resolve()
    if not resolved.is_relative_to(wiki) or not resolved.is_file():
        raise ValueError(f"Missing or escaping wiki file: {relative}")
    return resolved


def _active_term(index: str) -> str:
    active = []
    for block in re.split(r"(?m)(?=^#{1,3} )", index):
        heading, _, body = block.partition("\n")
        if not re.search(r"(?im)^.*\*\*Active term\*\*\s*$", body):
            continue
        match = re.match(
            r"^### \[(AY\d{4}-T[123])\]\(\1/_term-index\.md\)(?:\s|$)",
            heading,
        )
        if not match:
            raise ValueError("Active term must have a valid term-index heading")
        active.append(match[1])
    if len(active) != 1:
        raise ValueError("Expected exactly one active term in wiki/index.md")
    return active[0]


def _subject_rows(term_index: str) -> list[list[str]]:
    sections = re.split(r"(?m)^## ", term_index)
    subjects = [section for section in sections if section.partition("\n")[0].strip() == "Subjects"]
    if len(subjects) != 1:
        raise ValueError("Expected exactly one Subjects section")
    rows = []
    started = False
    finished = False
    for line in subjects[0].splitlines()[1:]:
        line = line.strip()
        if not line.startswith("|"):
            if started and line and not finished:
                if not (line.startswith("**Total Credits:**") or line == "---"):
                    raise ValueError("Unexpected content in Subjects table")
                finished = True
            continue
        if finished or not line.endswith("|"):
            raise ValueError("Malformed Subjects table")
        started = True
        rows.append([cell.strip() for cell in re.split(r"(?<!\\)\|", line[1:-1])])
    if len(rows) < 3:
        raise ValueError("Subjects table is missing or empty")
    header, separator, *data = rows
    if header != ["Code", "Subject", "Type", "Credits", "Section", "Schedule"]:
        raise ValueError("Unexpected Subjects table columns")
    if len(separator) != len(header) or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
        raise ValueError("Malformed Subjects table separator")
    if any(len(row) != len(header) for row in data):
        raise ValueError("Malformed subject row")
    return data


def read_subjects(wiki: Path) -> dict:
    wiki = wiki.resolve()
    term = _active_term(_wiki_file(wiki, "index.md").read_text(encoding="utf-8"))
    term_index = _wiki_file(wiki, f"{term}/_term-index.md").read_text(encoding="utf-8")
    subjects = []
    seen_codes = set()
    seen_paths = set()
    for code, link, kind, credits, section, schedule in _subject_rows(term_index):
        if not re.fullmatch(r"[A-Z][A-Z0-9-]*", code) or not re.fullmatch(r"[A-Z0-9]+", section):
            raise ValueError("Invalid subject code or section")
        if not all((kind, credits, schedule)):
            raise ValueError(f"Incomplete subject row: {code}")
        match = re.fullmatch(r"\[\[([^|\\]+)\\\|([^\]]+)\]\]", link)
        if not match:
            raise ValueError(f"Invalid subject overview link: {code}")
        target = match[1]
        if not re.fullmatch(r"[A-Za-z0-9-]+/_overview(?:\.md)?", target):
            raise ValueError(f"Unsafe subject overview path: {code}")
        relative = f"{term}/{target.removesuffix('.md')}.md"
        resolved = _wiki_file(wiki, relative)
        if not resolved.is_relative_to(wiki / term):
            raise ValueError(f"Subject overview escapes its term: {code}")
        normalized_code = code.replace("-", "")
        if normalized_code in seen_codes or resolved in seen_paths:
            raise ValueError(f"Duplicate subject: {code}")
        seen_codes.add(normalized_code)
        seen_paths.add(resolved)
        subjects.append({"code": code, "section": section, "overview": relative})
    return {"term": term, "subjects": subjects}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki", type=Path, default=Path.home() / "Documents/Obsidian/schoolMem/wiki")
    args = parser.parse_args(argv)
    try:
        manifest = read_subjects(args.wiki)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Canvas subjects: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
