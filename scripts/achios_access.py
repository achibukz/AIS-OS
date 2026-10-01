#!/usr/bin/env python3
"""Read shared achiOS services without depending on the current repository."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from achios_workspace import operator_home


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=["tasks", "calendar", "canvas", "recall"])
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    home = operator_home()
    if args.service == "tasks":
        import task_engine
        area = args.args[0] if len(args.args) == 1 else "all" if not args.args else None
        if area not in task_engine.FILTER_AREAS:
            parser.error("tasks accepts one area, all, or backlog")
        print(task_engine.render_tasks(task_engine.parse_tasks((ROOT / "tasks.md").read_text()), area=area))
        return 0
    if args.service == "recall":
        if args.args:
            parser.error("recall takes no arguments")
        import achimem_recall
        achimem_recall.VAULT = home / "Documents/Obsidian/achiMem"
        achimem_recall.SESSIONS = achimem_recall.VAULT / "raw/sessions"
        print(achimem_recall.build_context())
        return 0
    if args.service == "calendar":
        if not (args.args[:1] == ["agenda"] or args.args[:2] in (["calendars", "list"], ["events", "list"])):
            parser.error("calendar accepts agenda, calendars list, or events list")
        command = [sys.executable, str(ROOT / "scripts/gcal.py"), *args.args]
    else:
        reads = {"status", "courses", "due", "assignments", "detail", "grades", "announcements"}
        if not args.args or args.args[0] not in reads:
            parser.error("canvas requires a cached read command")
        db = Path(os.environ.get("ACHICORE_CANVAS_DB", str(home / ".local/state/achios/canvas/canvas.sqlite3")))
        if not db.is_file():
            print(json.dumps({"status": "error", "error": "canvas_cache_missing", "path": str(db)}))
            return 1
        command = [sys.executable, str(ROOT / "scripts/canvas.py"), "--db", str(db), *args.args]
    return subprocess.run(command, env={**os.environ, "ACHIOS_HOME": str(home)},
                          stdin=subprocess.DEVNULL).returncode


if __name__ == "__main__":
    raise SystemExit(main())
