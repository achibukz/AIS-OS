import sync_claude_memory as sync

MAC = "/Users/achibukz"
BOX = "/home/achibukz"


class TestRemapSlug:
    def test_rewrites_the_home_prefix(self):
        assert (
            sync.remap_slug("-Users-achibukz-Code-GitHub-AIS-OS", MAC, BOX)
            == "-home-achibukz-Code-GitHub-AIS-OS"
        )

    def test_keeps_dots_that_became_dashes(self):
        assert (
            sync.remap_slug("-Users-achibukz--local-share-achios-llm", MAC, BOX)
            == "-home-achibukz--local-share-achios-llm"
        )

    def test_home_itself_maps_cleanly(self):
        assert sync.remap_slug("-Users-achibukz", MAC, BOX) == "-home-achibukz"

    def test_returns_none_outside_home(self):
        assert sync.remap_slug("-tmp-scratch", MAC, BOX) is None


class TestMergeIndex:
    def test_keeps_server_only_entries(self):
        local = "# Memory Index\n\n- [A](a.md) — one\n"
        remote = "- [B](b.md) — two\n"
        assert sync.merge_index(local, remote) == (
            "# Memory Index\n\n- [A](a.md) — one\n- [B](b.md) — two\n"
        )

    def test_local_wins_on_a_shared_filename(self):
        local = "- [A new](a.md) — fresh\n"
        remote = "- [A old](a.md) — stale\n"
        assert sync.merge_index(local, remote) == "- [A new](a.md) — fresh\n"

    def test_unchanged_when_server_adds_nothing(self):
        local = "# Memory Index\n\n- [A](a.md) — one\n"
        assert sync.merge_index(local, "- [A](a.md) — dupe\n") == local

    def test_preserves_local_header_and_order(self):
        local = "# Memory Index\n\n- [B](b.md) — two\n- [A](a.md) — one\n"
        merged = sync.merge_index(local, "- [C](c.md) — three\n")
        assert merged.splitlines()[:4] == [
            "# Memory Index",
            "",
            "- [B](b.md) — two",
            "- [A](a.md) — one",
        ]
        assert merged.splitlines()[4] == "- [C](c.md) — three"

    def test_ignores_prose_lines_on_the_server(self):
        merged = sync.merge_index("- [A](a.md) — one\n", "just a note\n\n# Header\n")
        assert merged == "- [A](a.md) — one\n"

    def test_empty_local_takes_everything(self):
        assert sync.merge_index("", "- [B](b.md) — two\n") == "\n- [B](b.md) — two\n"


class TestMemoryDirs:
    def build(self, tmp_path):
        (tmp_path / "-Users-a-repo" / "memory").mkdir(parents=True)
        (tmp_path / "-Users-a-repo" / "tool-results").mkdir()
        (tmp_path / "-Users-a-secrets" / "memory").mkdir(parents=True)
        (tmp_path / "-Users-a-bare").mkdir()

    def test_returns_only_allowlisted_projects(self, tmp_path):
        self.build(tmp_path)
        found = sync.memory_dirs(tmp_path, "/Users/a", ["repo"])
        assert [d.parent.name for d in found] == ["-Users-a-repo"]

    def test_unlisted_project_memory_never_syncs(self, tmp_path):
        self.build(tmp_path)
        found = sync.memory_dirs(tmp_path, "/Users/a", ["repo"])
        assert all("secrets" not in d.parent.name for d in found)

    def test_ignores_transcript_siblings_of_memory(self, tmp_path):
        self.build(tmp_path)
        found = sync.memory_dirs(tmp_path, "/Users/a", ["repo"])
        assert [d.name for d in found] == ["memory"]

    def test_empty_allowlist_syncs_nothing(self, tmp_path):
        self.build(tmp_path)
        assert sync.memory_dirs(tmp_path, "/Users/a", []) == []

    def test_matches_the_real_aios_slug(self, tmp_path):
        (tmp_path / "-Users-achibukz-Code-GitHub-AIS-OS" / "memory").mkdir(parents=True)
        found = sync.memory_dirs(tmp_path, MAC, sync.PROJECTS)
        assert [d.parent.name for d in found] == ["-Users-achibukz-Code-GitHub-AIS-OS"]


class TestSlugify:
    def test_matches_observed_claude_naming(self):
        assert sync.slugify("/home/achibukz/.local/share/achios/llm") == (
            "-home-achibukz--local-share-achios-llm"
        )
