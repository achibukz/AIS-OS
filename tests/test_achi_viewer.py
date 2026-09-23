import html
import os
import re
import socket
import threading
import urllib.parse
from http.server import ThreadingHTTPServer
from pathlib import Path
import pytest
import requests

import achi_viewer


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault with structured notes, subdirectories, and .obsidian marker."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()

    # Subdirectories
    sub1 = vault / "folder_a"
    sub1.mkdir()
    sub2 = vault / "folder_b"
    sub2.mkdir()
    sub_unicode = vault / "日本語_dir"
    sub_unicode.mkdir()

    # Notes
    (vault / "root_note.md").write_text("# Root Note\n\nContent here.", encoding="utf-8")
    (vault / "Note With Spaces.md").write_text("# Heading One\n\n## Sub Heading (Detail!)\n\nText.", encoding="utf-8")
    (sub1 / "clash.md").write_text("# Clash in A\n\nContent A.", encoding="utf-8")
    (sub2 / "clash.md").write_text("# Clash in B\n\nContent B.", encoding="utf-8")
    (sub1 / "unique_sub.md").write_text("# Unique Sub\n\n## Section Alpha\n\nHello.", encoding="utf-8")
    (sub_unicode / "日本語 ノート.md").write_text("# 概要\n\n## 詳細 データ\n\nUnicode content.", encoding="utf-8")

    # Non-markdown asset
    (vault / "attachment.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    # Blocked sensitive file inside vault
    (vault / ".env").write_text("SECRET=123", encoding="utf-8")

    # File outside vault
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n\nShould not be accessible.", encoding="utf-8")

    # Symlinks
    # 1. Symlink inside vault pointing outside vault
    (vault / "symlink_outside.md").symlink_to(outside)
    # 2. Symlink inside vault pointing to valid file inside vault
    (vault / "symlink_valid.md").symlink_to(sub1 / "unique_sub.md")
    # 3. Symlink inside vault pointing to blocked file
    (vault / "symlink_blocked.md").symlink_to(vault / ".env")

    return vault


def test_slugify_heading():
    """Verify heading slugification matches GitHub/Obsidian anchor rules for ASCII and Unicode."""
    assert achi_viewer.slugify_heading("My Heading") == "my-heading"
    assert achi_viewer.slugify_heading("Heading 1: Overview (Draft!)") == "heading-1-overview-draft"
    assert achi_viewer.slugify_heading("Multiple   --- Spaces --") == "multiple-spaces"
    assert achi_viewer.slugify_heading("測試 見出し") == "測試-見出し"
    assert achi_viewer.slugify_heading("Éléments et Résumé") == "éléments-et-résumé"
    assert achi_viewer.slugify_heading("# Leading Hash Marks ###") == "leading-hash-marks"


def test_find_vault(temp_vault, tmp_path):
    """Verify vault discovery finds enclosing vault with .obsidian or .git, and respects boundaries."""
    child_file = temp_vault / "folder_a" / "unique_sub.md"
    assert achi_viewer.find_vault(child_file, root_dir=tmp_path) == temp_vault.resolve()

    # Git-based vault fixture
    git_vault = tmp_path / "git_vault"
    git_vault.mkdir()
    (git_vault / ".git").mkdir()
    git_file = git_vault / "sub" / "note.md"
    git_file.parent.mkdir()
    git_file.write_text("Hello", encoding="utf-8")
    assert achi_viewer.find_vault(git_file, root_dir=tmp_path) == git_vault.resolve()

    # Outside vault
    outside_file = tmp_path / "outside.md"
    assert achi_viewer.find_vault(outside_file, root_dir=tmp_path) is None


def test_wikilink_note_alias_heading(temp_vault, tmp_path):
    """Verify supported wikilinks open intended note in same vault and preserve aliases and heading anchors."""
    source_file = temp_vault / "root_note.md"

    # 1. Simple note
    md = "Link to [[unique_sub]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md">unique_sub</a>' in res

    # 2. Note with alias
    md = "Link to [[unique_sub|Custom Label]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md">Custom Label</a>' in res

    # 3. Note with heading anchor
    md = "Link to [[unique_sub#Section Alpha]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md#section-alpha">unique_sub#Section Alpha</a>' in res

    # 4. Note with heading anchor and alias
    md = "Link to [[unique_sub#Section Alpha|Alpha Section]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md#section-alpha">Alpha Section</a>' in res

    # 5. Same-file heading anchor
    md = "Jump to [[#Heading One]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="#heading-one">#Heading One</a>' in res

    # 6. Same-file heading anchor with alias
    md = "Jump to [[#Heading One|Top of Page]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="#heading-one">Top of Page</a>' in res


def test_wikilink_duplicate_basenames(temp_vault, tmp_path):
    """Ambiguous basenames must remain visibly unresolved rather than point to an arbitrary file."""
    source_file = temp_vault / "root_note.md"

    # 'clash' exists in both folder_a and folder_b
    md = "Refer to [[clash]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[clash]]</span>' in res
    assert "<a " not in res

    # With alias: should remain unresolved and preserve display label
    md = "Refer to [[clash|Ambiguous Note]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[Ambiguous Note]]</span>' in res
    assert "<a " not in res

    # Disambiguated with path: should resolve safely
    md = "Refer to [[folder_a/clash]] and [[folder_b/clash|Clash B]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/folder_a/clash.md">folder_a/clash</a>' in res
    assert '<a class="wiki-link" href="/test_vault/folder_b/clash.md">Clash B</a>' in res


def test_wikilink_missing_note(temp_vault, tmp_path):
    """Missing notes must remain visibly unresolved rather than point to an arbitrary file."""
    source_file = temp_vault / "root_note.md"

    md = "Check [[missing_note]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[missing_note]]</span>' in res
    assert "<a " not in res

    md = "Check [[nonexistent_path/note|My Label]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[My Label]]</span>' in res
    assert "<a " not in res


def test_wikilink_unicode_and_spaces(temp_vault, tmp_path):
    """Relative paths, Unicode and spaces must resolve safely with proper URL quoting."""
    source_file = temp_vault / "root_note.md"

    # Spaces in note name
    md = "See [[Note With Spaces#Sub Heading (Detail!)|Sub Detail]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/Note%20With%20Spaces.md#sub-heading-detail">Sub Detail</a>' in res

    # Unicode in folder and note name
    md = "See [[日本語_dir/日本語 ノート#詳細 データ|詳細]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    quoted_url = urllib.parse.quote("/test_vault/日本語_dir/日本語 ノート.md", safe="/")
    assert f'<a class="wiki-link" href="{quoted_url}#詳細-データ">詳細</a>' in res

    # Bare Unicode basename
    md = "See [[日本語 ノート]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert f'<a class="wiki-link" href="{quoted_url}">日本語 ノート</a>' in res


def test_wikilink_traversal_and_encoding_blocked(temp_vault, tmp_path):
    """Traversal, encoded escape and symlink targets cannot bypass protected-path rules or cross vault boundary."""
    source_file = temp_vault / "root_note.md"

    # Direct traversal
    md = "Sneak [[../../outside.md]] and [[../outside]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[../../outside.md]]</span>' in res
    assert '<span class="wiki-link unresolved is-unresolved">[[../outside]]</span>' in res
    assert "<a " not in res

    # Encoded traversal escape
    md = "Sneak [[%2e%2e%2foutside.md]] and [[..%2foutside]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">' in res
    assert "<a " not in res

    # Blocked resource inside vault
    md = "Read [[.env]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[.env]]</span>' in res
    assert "<a " not in res


def test_wikilink_symlinks(temp_vault, tmp_path):
    """Symlink targets pointing outside vault or to blocked files must remain unresolved; internal valid symlinks resolve."""
    source_file = temp_vault / "root_note.md"

    # Symlink pointing outside vault
    md = "Follow [[symlink_outside]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[symlink_outside]]</span>' in res
    assert "<a " not in res

    # Symlink pointing to blocked file
    md = "Follow [[symlink_blocked]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<span class="wiki-link unresolved is-unresolved">[[symlink_blocked]]</span>' in res
    assert "<a " not in res

    # Symlink pointing to valid note inside vault
    md = "Follow [[symlink_valid|Valid Symlink]]."
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md">Valid Symlink</a>' in res


def test_normal_markdown_intact(temp_vault, tmp_path):
    """Existing Markdown links and formatting remain intact and are not treated as wikilinks."""
    source_file = temp_vault / "root_note.md"

    md = (
        "Here is a [Normal Link](https://example.com) and [Local Note](unique_sub.md).\n"
        "Anchor: [Heading Link](#heading-one).\n"
        "Image: ![Logo](attachment.png).\n"
        "Wikilink: [[unique_sub]]."
    )
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)

    # Markdown links remain exactly as written
    assert "[Normal Link](https://example.com)" in res
    assert "[Local Note](unique_sub.md)" in res
    assert "[Heading Link](#heading-one)" in res
    assert "![Logo](attachment.png)" in res
    # Wikilink was converted
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md">unique_sub</a>' in res


def test_code_blocks_protected(temp_vault, tmp_path):
    """Code blocks and inline code containing wikilink syntax must not be transformed."""
    source_file = temp_vault / "root_note.md"

    md = (
        "Inline `[[not_a_link]]` should stay.\n\n"
        "```markdown\n"
        "Fenced code: [[also_not_a_link|Alias]]\n"
        "```\n\n"
        "Actual: [[unique_sub]]."
    )
    res = achi_viewer.resolve_wikilinks(md, file_path=source_file, vault_root=temp_vault, root_dir=tmp_path)

    assert "`[[not_a_link]]`" in res
    assert "Fenced code: [[also_not_a_link|Alias]]" in res
    assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md">unique_sub</a>' in res


def test_http_server_renders_wikilinks_and_serves_notes(temp_vault, tmp_path, monkeypatch):
    """Live HTTP integration test verifying note rendering with wikilinks and document access."""
    # Point achi_viewer.ROOT_DIR to tmp_path
    monkeypatch.setattr(achi_viewer, "ROOT_DIR", tmp_path.resolve())

    # Create a test note with various wikilinks
    test_note = temp_vault / "hub.md"
    test_note.write_text(
        "# Hub Note\n\n"
        "- Good link: [[unique_sub|Sub note]]\n"
        "- Missing link: [[ghost_note]]\n"
        "- Ambiguous link: [[clash]]\n"
        "- Traversal: [[../../outside.md]]\n"
        "- Normal link: [External](https://google.com)\n",
        encoding="utf-8"
    )

    # Start ephemeral HTTP server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = ThreadingHTTPServer(("127.0.0.1", port), achi_viewer.AchiViewerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{port}"
        h = {"Connection": "close"}

        # 1. Fetch rendered markdown
        r = requests.get(f"{base_url}/test_vault/hub.md", headers=h)
        assert r.status_code == 200
        text = html.unescape(r.text)
        # Check resolved wikilink in markdown-source or rendered HTML
        assert '<a class="wiki-link" href="/test_vault/folder_a/unique_sub.md">Sub note</a>' in text
        # Check unresolved spans
        assert '<span class="wiki-link unresolved is-unresolved">[[ghost_note]]</span>' in text
        assert '<span class="wiki-link unresolved is-unresolved">[[clash]]</span>' in text
        assert '<span class="wiki-link unresolved is-unresolved">[[../../outside.md]]</span>' in text

        # 2. Follow the resolved link
        r_target = requests.get(f"{base_url}/test_vault/folder_a/unique_sub.md", headers=h)
        assert r_target.status_code == 200
        assert "Unique Sub" in r_target.text

        # 3. Raw mode returns untouched markdown with [[wikilinks]]
        r_raw = requests.get(f"{base_url}/test_vault/hub.md?raw=true", headers=h)
        assert r_raw.status_code == 200
        assert "[[unique_sub|Sub note]]" in r_raw.text

        # 4. Blocked files return 403
        r_blocked = requests.get(f"{base_url}/test_vault/.env", headers=h)
        assert r_blocked.status_code == 403

        # 5. Nonexistent file returns 404
        r_404 = requests.get(f"{base_url}/test_vault/nonexistent_xyz.md", headers=h)
        assert r_404.status_code == 404
    finally:
        server.shutdown()
        server.server_close()
