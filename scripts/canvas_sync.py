"""Fetch complete Canvas categories before replacing saved facts."""
import json

from canvas_client import CanvasError, timestamp
from canvas_store import CATEGORIES, configure_courses, project_record, save_auth, save_failure, save_snapshot
from canvas_subjects import read_subjects


def load_mapping(config, wiki):
    mapping = json.loads((config / "mappings.json").read_text())
    manifest = read_subjects(wiki)
    if (mapping.get("term") != manifest["term"] or type(mapping.get("user_id")) is not int
            or mapping["user_id"] <= 0 or not isinstance(mapping.get("subjects"), list)):
        raise CanvasError("mapping_requires_verification")
    expected = [(s["code"], s["section"], s["overview"]) for s in manifest["subjects"]]
    actual = [(s.get("code"), s.get("section"), s.get("overview")) for s in mapping["subjects"]]
    if actual != expected or any(type(s.get("course_id")) is not int or s["course_id"] <= 0 for s in mapping["subjects"]):
        raise CanvasError("mapping_requires_verification")
    if len({s["course_id"] for s in mapping["subjects"]}) != len(expected):
        raise CanvasError("mapping_requires_verification")
    return mapping


def fetch_category(client, course_id, category):
    base = f"/api/v1/courses/{course_id}"
    if category == "courses":
        row, _ = client.get(base)
        return [row]
    if category == "assignments":
        return client.list(base + "/assignments?include[]=submission&per_page=100")
    if category == "grades":
        return client.list(base + "/enrollments?user_id=self&type[]=StudentEnrollment&per_page=100")
    return client.list(base + "/discussion_topics?only_announcements=true&per_page=100")


def sync(client, db, mapping):
    configure_courses(db, mapping)
    failures = []
    try:
        profile, _ = client.get("/api/v1/users/self/profile")
        if not isinstance(profile, dict) or profile.get("id") != mapping["user_id"]:
            raise CanvasError("account_changed")
    except CanvasError as exc:
        if exc.kind == "authentication_expired":
            save_auth(db, "expired", timestamp())
        for subject in mapping["subjects"]:
            for category in CATEGORIES:
                save_failure(db, subject["course_id"], category, exc.kind, timestamp())
        return {"error": exc.kind, "complete_categories": 0}
    save_auth(db, "valid", timestamp())
    complete = 0
    expired = False
    for subject in mapping["subjects"]:
        course_id = subject["course_id"]
        for category in CATEGORIES:
            try:
                if expired:
                    raise CanvasError("authentication_expired")
                raw = fetch_category(client, course_id, category)
                records = [project_record(category, row, course_id, mapping["user_id"]) for row in raw]
                save_snapshot(db, course_id, category, records, timestamp())
                complete += 1
            except CanvasError as exc:
                if exc.kind == "authentication_expired":
                    expired = True
                    save_auth(db, "expired", timestamp())
                save_failure(db, course_id, category, exc.kind, timestamp())
                failures.append({"subject": subject["code"], "category": category, "error": exc.kind})
    return {"complete_categories": complete, "failures": failures}
