#!/usr/bin/env python3
"""Link the achiOS skills into user skill directories without replacing existing skills."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ("achios-google", "achios-planning", "achios-canvas", "achios-recall")
TARGETS = {"codex": ".agents/skills", "claude": ".claude/skills", "agy": ".gemini/config/skills",
           "skillshare": ".config/skillshare/skills"}


def install(home: Path, targets: list[str], *, dry_run: bool = False) -> list[dict]:
    links = [(ROOT / "skills" / name, home / TARGETS[target] / name)
             for target in targets for name in SKILLS]
    for source, destination in links:
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing skill: {source}")
        if destination.is_symlink() and destination.resolve() == source.resolve():
            continue
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Existing skill left intact: {destination}")
    receipt = []
    for source, destination in links:
        exists = destination.is_symlink()
        if not dry_run and not exists:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(source, target_is_directory=True)
        receipt.append({"path": str(destination), "source": str(source),
                        "status": "present" if exists else "planned" if dry_run else "linked"})
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=TARGETS, action="append")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps({"skills": install(Path.home(), args.target or ["codex", "claude"],
                                           dry_run=args.dry_run)}))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
