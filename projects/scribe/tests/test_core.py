from datetime import date

from core import format_timestamp, group_segments, output_path, parse_segment, slugify


def test_parse_segment_valid():
    line = "[00:01:05.000 --> 00:01:09.480]   Kaya naman po, let's start the lecture."
    assert parse_segment(line) == (65, 69, "Kaya naman po, let's start the lecture.")


def test_parse_segment_rejects_noise():
    assert parse_segment("whisper_init_state: compute buffer") is None
    assert parse_segment("") is None


def test_format_timestamp():
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(3725) == "01:02:05"


def test_slugify():
    assert slugify("CSOPESY Lecture 5 (final).mp4".rsplit(".", 1)[0]) == "csopesy-lecture-5-final"
    assert slugify("///") == "untitled"


def test_output_path_date_prefix(tmp_path):
    p = output_path(tmp_path, "Lecture Recording.mp4", on=date(2026, 7, 18))
    assert p.name == "2026-07-18-lecture-recording.md"


def test_output_path_collision_suffix(tmp_path):
    on = date(2026, 7, 18)
    first = output_path(tmp_path, "lecture.mp4", on=on)
    first.write_text("x")
    second = output_path(tmp_path, "lecture.mp4", on=on)
    second.write_text("x")
    third = output_path(tmp_path, "lecture.mp4", on=on)
    assert first.name == "2026-07-18-lecture.md"
    assert second.name == "2026-07-18-lecture-2.md"
    assert third.name == "2026-07-18-lecture-3.md"


def test_group_segments_collapses_repeats():
    segments = [(0, 2, "yung kasama na siya")] * 5 + [(10, 12, "tapos yun na")]
    body = group_segments(segments, window=60)
    assert body == "[00:00:00] yung kasama na siya tapos yun na"


def test_group_segments_windows():
    segments = [(0, 5, "one"), (30, 35, "two"), (65, 70, "three"), (70, 75, "")]
    body = group_segments(segments, window=60)
    assert body == "[00:00:00] one two\n\n[00:01:05] three"
