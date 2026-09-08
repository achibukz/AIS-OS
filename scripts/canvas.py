#!/usr/bin/env python3
"""Query cached Canvas facts or run an explicit coordinator-owned refresh."""
from __future__ import annotations

import argparse
import json
import sys
import sqlite3
from pathlib import Path

from canvas_client import CONFIG, CanvasClient, CanvasError, atomic_write, match_courses, timestamp
from canvas_subjects import read_subjects
from canvas_store import DATABASE, open_reader, open_writer, query
from canvas_sync import load_mapping, sync

WIKI = Path.home() / "Documents/Obsidian/schoolMem/wiki"


def verify_mapping(client, wiki):
    manifest = read_subjects(wiki)
    profile, _ = client.get("/api/v1/users/self/profile")
    if not isinstance(profile, dict) or type(profile.get("id")) is not int:
        raise CanvasError("malformed_profile")
    courses = client.list("/api/v1/courses?include[]=term&per_page=100")
    mapping = {**match_courses(manifest, courses), "user_id": profile["id"]}
    atomic_write(client.config / "mappings.json", json.dumps(mapping))
    return {"term": mapping["term"], "mapped_subjects": len(mapping["subjects"]), "verified_at": mapping["verified_at"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--wiki", type=Path, default=WIKI)
    parser.add_argument("--db", type=Path, default=DATABASE)
    parser.add_argument("--course")
    parser.add_argument("--id", type=int)
    parser.add_argument("--period", choices=["week", "next-seven-days"], default="week")
    parser.add_argument("--unfinished", action="store_true")
    parser.add_argument("command", choices=["probe", "map", "sync", "status", "courses", "due",
                                            "assignments", "detail", "grades", "announcements"])
    args = parser.parse_args(argv)
    try:
        if args.command not in ("probe", "map", "sync"):
            if args.command == "detail" and (args.id is None or args.course is None):
                raise CanvasError("detail_requires_course_and_id")
            with open_reader(args.db) as db:
                result = query(db, args.command, course=args.course, item=args.id,
                               period=args.period, unfinished=args.unfinished)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        with CanvasClient(args.config) as client:
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
            atomic_write(args.config / "receipt.json", json.dumps(result))
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
