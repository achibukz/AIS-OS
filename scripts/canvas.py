#!/usr/bin/env python3
"""Query cached Canvas facts or run an explicit coordinator-owned refresh."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from canvas_client import CONFIG, CanvasClient, CanvasError, atomic_write, match_courses, timestamp, writer_lock
from canvas_subjects import read_subjects
from canvas_store import DATABASE, open_reader, open_writer, query, save_auth
from canvas_sync import load_mapping, sync
from canvas_events import deliver, preview

WIKI = Path.home() / "Documents/Obsidian/schoolMem/wiki"


def verify_mapping(client, wiki):
    manifest = read_subjects(wiki)
    profile, _ = client.get("/api/v1/users/self/profile")
    if not isinstance(profile, dict) or type(profile.get("id")) is not int:
        raise CanvasError("malformed_profile")
    courses = client.list("/api/v1/courses?include[]=term&per_page=100")
    candidates = [{"id": c.get("id"), "course_code": c.get("course_code"),
                   "name": c.get("name"), "term": c.get("term")} for c in courses]
    atomic_write(client.config / "course-candidates.json", json.dumps(candidates))
    mapping = {**match_courses(manifest, courses), "user_id": profile["id"]}
    atomic_write(client.config / "mappings.json", json.dumps(mapping))
    return {"term": mapping["term"], "mapped_subjects": len(mapping["subjects"]), "verified_at": mapping["verified_at"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--wiki", type=Path, default=WIKI)
    parser.add_argument("--db", type=Path, default=DATABASE)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int)
    parser.add_argument("--course")
    parser.add_argument("--id", type=int)
    parser.add_argument("--period", choices=["week", "next-seven-days"])
    parser.add_argument("--unfinished", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send pending events through achiSchooNounce")
    parser.add_argument("command", choices=["probe", "map", "sync", "status", "courses", "due",
                                            "assignments", "detail", "grades", "announcements", "deliver"])
    args = parser.parse_args(argv)
    try:
        if args.send and args.command != "deliver":
            raise CanvasError("send_requires_deliver")
        allowed = {
            "limit": {"courses", "assignments", "grades", "announcements", "due"},
            "offset": {"courses", "assignments", "grades", "announcements", "due"},
            "period": {"due"}, "unfinished": {"due", "assignments"},
            "course": {"status", "courses", "assignments", "detail", "grades", "announcements", "due"},
            "id": {"detail", "announcements"},
        }
        for flag, commands in allowed.items():
            value = getattr(args, flag)
            if value is not None and value is not False and args.command not in commands:
                raise CanvasError(f"{flag}_not_supported_for_command")
        if args.command == "deliver":
            if args.send:
                if not args.db.is_file():
                    raise CanvasError("database_unavailable")
                with writer_lock(args.config), open_writer(args.db) as db:
                    result = deliver(db)
            else:
                with open_reader(args.db) as db:
                    result = preview(db)
            print(json.dumps(result, ensure_ascii=False))
            return 1 if result.get("error") else 0
        if args.command not in ("probe", "map", "sync"):
            if args.command == "detail" and (args.id is None or args.course is None):
                raise CanvasError("detail_requires_course_and_id")
            with open_reader(args.db) as db:
                result = query(db, args.command, course=args.course, item=args.id,
                               period=args.period or "week", unfinished=args.unfinished,
                               limit=args.limit if args.limit is not None else 50, offset=args.offset or 0)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        with CanvasClient(args.config) as client:
            try:
                if args.command == "map":
                    result = verify_mapping(client, args.wiki)
                elif args.command == "sync":
                    mapping = load_mapping(args.config, args.wiki)
                    with open_writer(args.db) as db:
                        result = sync(client, db, mapping)
                else:
                    profile, _ = client.get("/api/v1/users/self/profile")
                    if not isinstance(profile, dict) or type(profile.get("id")) is not int:
                        raise CanvasError("malformed_profile")
                    result = {"authentication": "valid", "checked_at": timestamp()}
                if args.command in ("probe", "map"):
                    with open_writer(args.db) as db:
                        save_auth(db, "valid", timestamp())
                atomic_write(args.config / "receipt.json", json.dumps(result))
            except CanvasError as exc:
                if exc.kind == "authentication_expired" and args.command != "sync":
                    try:
                        with open_writer(args.db) as db:
                            save_auth(db, "expired", timestamp())
                    except (CanvasError, OSError, sqlite3.Error):
                        pass
                atomic_write(args.config / "receipt.json", json.dumps({"command": args.command,
                             "error": exc.kind, "checked_at": timestamp()}))
                raise

    except CanvasError as exc:
        print(json.dumps({"error": exc.kind}), file=sys.stderr)
        return 1
    except (OSError, ValueError, sqlite3.Error):
        print(json.dumps({"error": "invalid_or_unavailable_local_data"}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result.get("error") or result.get("failures") else 0


if __name__ == "__main__":
    raise SystemExit(main())
