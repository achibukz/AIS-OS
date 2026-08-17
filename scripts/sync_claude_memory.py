#!/usr/bin/env python3
"""Push Claude Code's per-project memory from this Mac to the headless server.

Three things make this more than an rsync of ~/.claude/projects/:

- The project directory name is a slug of the repo's absolute path, so the Mac's
  `-Users-achibukz-Code-GitHub-AIS-OS` is not the directory the server reads. It
  gets remapped to `-home-achibukz-...` on the way over.
- `projects/` also holds full session transcripts. Only `memory/` is ever sent.
- The server writes its own memories. This merges rather than mirrors: no
  --delete, and MEMORY.md is unioned so the server's own index lines survive.

One-way, Mac to server.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_HOST = "achibuntu"
REMOTE_HOME = "/home/achibukz"
INDEX = "MEMORY.md"

# Allowlist of project paths relative to $HOME, same principle as sync-claude-config.sh.
# Only achiOS memory is operating rules the server needs. Other projects' memory carries
# personal data — schoolMem holds Aki's full name and student ID — and the server runs a
# sub-70B model autonomously with Telegram reach, so anything landing there is readable
# by a model nobody is supervising.
PROJECTS = ["Code/GitHub/AIS-OS"]
ENTRY_RE = re.compile(r"^- \[[^\]]*\]\(([^)]+)\)")


def slugify(path: str) -> str:
    """Mirror how Claude Code names a project directory from an absolute path."""
    return path.replace("/", "-").replace(".", "-")


def remap_slug(slug: str, local_home: str, remote_home: str) -> str | None:
    """Rewrite a local project slug into the server's. None if it is not under $HOME."""
    prefix = slugify(local_home)
    if not slug.startswith(prefix):
        return None
    return slugify(remote_home) + slug[len(prefix) :]


def merge_index(local: str, remote: str) -> str:
    """Union two MEMORY.md indexes, keyed by the linked filename.

    Local wins on a shared filename; entries only the server knows about are kept.
    The local header and ordering are preserved.
    """
    local_files = {
        m.group(1) for line in local.splitlines() if (m := ENTRY_RE.match(line))
    }
    extra = [
        line
        for line in remote.splitlines()
        if (m := ENTRY_RE.match(line)) and m.group(1) not in local_files
    ]
    if not extra:
        return local
    return local.rstrip("\n") + "\n" + "\n".join(extra) + "\n"


def memory_dirs(projects: Path, home: str, allowed: list[str]) -> list[Path]:
    wanted = {slugify(f"{home}/{rel}") for rel in allowed}
    return sorted(
        d for d in projects.glob("*/memory") if d.is_dir() and d.parent.name in wanted
    )


def read_remote(host: str, path: str) -> str:
    done = subprocess.run(
        ["ssh", host, f"cat {path} 2>/dev/null || true"],
        capture_output=True,
        text=True,
    )
    return done.stdout


def sync_dir(host: str, local: Path, remote_dir: str, dry_run: bool) -> None:
    subprocess.run(["ssh", host, f"mkdir -p {remote_dir}"], check=True)

    merged = merge_index(
        (local / INDEX).read_text() if (local / INDEX).exists() else "",
        read_remote(host, f"{remote_dir}/{INDEX}"),
    )

    flags = ["-az"] + (["--dry-run", "-v"] if dry_run else [])
    subprocess.run(
        [
            "rsync",
            *flags,
            f"--exclude={INDEX}",
            "--include=*.md",
            "--exclude=*",
            f"{local}/",
            f"{host}:{remote_dir}/",
        ],
        check=True,
    )

    if dry_run:
        print(f"  would write {remote_dir}/{INDEX} ({len(merged.splitlines())} lines)")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".md") as tmp:
        tmp.write(merged)
        tmp.flush()
        subprocess.run(
            ["rsync", "-az", tmp.name, f"{host}:{remote_dir}/{INDEX}"], check=True
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--remote-home", default=REMOTE_HOME)
    args = parser.parse_args()

    local_home = str(Path.home())
    projects = Path(local_home) / ".claude" / "projects"
    if not projects.is_dir():
        print("no ~/.claude/projects, nothing to sync")
        return 0

    for local in memory_dirs(projects, local_home, PROJECTS):
        slug = remap_slug(local.parent.name, local_home, args.remote_home)
        if slug is None:
            print(f"skip {local.parent.name} (not under $HOME)")
            continue
        remote_dir = f"{args.remote_home}/.claude/projects/{slug}/memory"
        print(f"memory: {local.parent.name} -> {slug}", flush=True)
        sync_dir(args.host, local, remote_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
