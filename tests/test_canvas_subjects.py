import json
import pytest

from canvas_subjects import main, read_subjects


TERM = "AY2627-T1"
ROW = r"| STDISCM | [[STDISCM-Distributed-Computing/_overview\|Distributed Computing]] | Lecture | 3.00 | S03 | TUE/FRI |"


@pytest.fixture
def wiki(tmp_path):
    root = tmp_path / "wiki"
    subject = root / TERM / "STDISCM-Distributed-Computing"
    subject.mkdir(parents=True)
    (subject / "_overview.md").write_text("# Distributed Computing\n")
    (root / "index.md").write_text(
        "### [AY2526-T3](AY2526-T3/_term-index.md) Previous\n\n"
        "**Completed**\n\n"
        f"### [{TERM}]({TERM}/_term-index.md) Current\n\n"
        "**Year Level:** 4 | **Credits:** 14.00 | **Active term**\n"
    )
    (root / TERM / "_term-index.md").write_text(
        "# Term\n\n## Subjects\n\n"
        "| Code | Subject | Type | Credits | Section | Schedule |\n"
        "|------|---------|------|---------|---------|----------|\n"
        + ROW + "\n\n**Total Credits:** 3.00\n\n> Room correction from orientation.\n\n## Weekly Schedule\n"
        "| ignored | table |\n"
    )
    return root


def test_reads_active_term_and_escaped_link_without_writes(wiki):
    before = {p: p.read_bytes() for p in wiki.rglob("*") if p.is_file()}
    assert read_subjects(wiki) == {
        "term": TERM,
        "subjects": [{"code": "STDISCM", "section": "S03", "overview": f"{TERM}/STDISCM-Distributed-Computing/_overview.md"}],
    }
    assert {p: p.read_bytes() for p in wiki.rglob("*") if p.is_file()} == before


def test_rollover_follows_marker_not_directory_order(wiki):
    next_term = "AY2627-T2"
    (wiki / TERM).rename(wiki / next_term)
    index = wiki / "index.md"
    index.write_text(index.read_text().replace(TERM, next_term))
    (wiki / "AY9999-T3").mkdir()
    assert read_subjects(wiki)["term"] == next_term


@pytest.mark.parametrize("change", [
    lambda text: text.replace("**Active term**", "**Completed**"),
    lambda text: text.replace("**Completed**", "**Active term**"),
    lambda text: text.replace(f"({TERM}/_term-index.md)", "(../outside.md)"),
])
def test_rejects_missing_ambiguous_or_unsafe_active_term(wiki, change):
    index = wiki / "index.md"
    index.write_text(change(index.read_text()))
    with pytest.raises(ValueError):
        read_subjects(wiki)


@pytest.mark.parametrize("replacement", [
    "",
    ROW + "\n" + ROW,
    ROW.replace("S03", ""),
    ROW.replace("3.00 |", ""),
    ROW + "\n" + ROW.lstrip("|"),
    ROW + "\n" + ROW.rstrip("|"),
    ROW.replace(r"\|Distributed Computing", "|Distributed Computing"),
    ROW.replace("STDISCM-Distributed-Computing/_overview", "../../outside"),
    ROW.replace("STDISCM-Distributed-Computing/_overview", "/tmp/outside"),
    ROW.replace("STDISCM-Distributed-Computing/_overview", "Missing/_overview"),
])
def test_rejects_invalid_rows_instead_of_returning_partial_manifest(wiki, replacement):
    term_index = wiki / TERM / "_term-index.md"
    term_index.write_text(term_index.read_text().replace(ROW, replacement))
    with pytest.raises(ValueError):
        read_subjects(wiki)


def test_rejects_overview_symlink_outside_vault(wiki, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("outside")
    overview = wiki / TERM / "STDISCM-Distributed-Computing/_overview.md"
    overview.unlink()
    overview.symlink_to(outside)
    with pytest.raises(ValueError, match="escaping"):
        read_subjects(wiki)


def test_rejects_duplicate_subject_codes_with_different_overviews(wiki):
    other = wiki / TERM / "Other/_overview.md"
    other.parent.mkdir()
    other.write_text("other")
    index = wiki / TERM / "_term-index.md"
    second = ROW.replace("| STDISCM |", "| ST-DISCM |")
    second = second.replace("STDISCM-Distributed-Computing/_overview", "Other/_overview")
    index.write_text(index.read_text().replace(ROW, ROW + "\n" + second))
    with pytest.raises(ValueError, match="Duplicate"):
        read_subjects(wiki)


def test_rejects_overview_symlink_into_another_term(wiki):
    old = wiki / "AY2526-T3/old.md"
    old.parent.mkdir()
    old.write_text("old subject")
    overview = wiki / TERM / "STDISCM-Distributed-Computing/_overview.md"
    overview.unlink()
    overview.symlink_to(old)
    with pytest.raises(ValueError, match="escapes its term"):
        read_subjects(wiki)


@pytest.mark.parametrize("change", [
    lambda text: text.replace("## Subjects", "## Courses"),
    lambda text: text.replace("| Section |", "| Group |"),
    lambda text: text.replace("|------|", "|bad|"),
    lambda text: text + "\n## Subjects\n",
])
def test_rejects_invalid_table_structure(wiki, change):
    index = wiki / TERM / "_term-index.md"
    index.write_text(change(index.read_text()))
    with pytest.raises(ValueError):
        read_subjects(wiki)


def test_cli_returns_json(wiki, capsys):
    assert main(["--wiki", str(wiki)]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["subjects"][0]["code"] == "STDISCM"
    assert output.err == ""


def test_cli_failure_has_no_partial_output(wiki, capsys):
    (wiki / TERM / "STDISCM-Distributed-Computing/_overview.md").unlink()
    assert main(["--wiki", str(wiki)]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Missing" in output.err
