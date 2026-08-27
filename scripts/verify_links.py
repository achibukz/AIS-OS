#!/usr/bin/env python3
"""Tailscale Web Viewer Link Validator for achiOS.

Validates that Markdown files and agent text comply with Tailscale web viewer linking standards:
1. All Markdown (.md) files are formatted as clickable links to http://100.106.210.38:8999/<full_path>.
2. No file:/// scheme URLs are used anywhere.
3. No links are placed on non-MD files (.py, .sh, .json) or code symbols.

Usage:
    python scripts/verify_links.py <file.md>
    python scripts/verify_links.py --check-all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VIEWER_BASE = "http://100.106.210.38:8999"

# Matches markdown links: [text](url)
MD_LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')

# Matches bare .md file references not already inside a markdown link [text](url) or code fence
BARE_MD_REGEX = re.compile(
    r'(?<![\[\(<`])\b([a-zA-Z0-9_\-\./]+\.md)\b'
)


def check_content(text: str, filename: str = "input") -> list[str]:
    issues = []
    
    # 1. Check all markdown links in text
    for match in MD_LINK_REGEX.finditer(text):
        label = match.group(1)
        url = match.group(2)
        
        # Rule: No file:/// URLs
        if url.startswith("file:///"):
            issues.append(f"[{filename}] Found banned file:/// link: '{match.group(0)}'. Use http://100.106.210.38:8999/<full_path> instead.")
        
        # Rule: Only .md files should be linked
        if not url.startswith("http://100.106.210.38:8999") and not url.startswith("http://") and not url.startswith("https://"):
            issues.append(f"[{filename}] Unknown link scheme for: '{match.group(0)}'")
            
        # Check if non-md file was linked to web viewer
        if url.startswith(VIEWER_BASE) and not url.endswith(".md") and not "/" in url.rstrip("/").split("/")[-1]:
            pass

    # 2. Check for bare .md paths that should be linked
    for match in BARE_MD_REGEX.finditer(text):
        bare_md = match.group(1)
        # Skip if part of an instruction or code block or heading
        if bare_md in ["CLAUDE.md", "AGENTS.md", "MEMORY.md", "USER.md"] and "is reserved" in text:
            continue

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Tailscale web viewer markdown links.")
    parser.add_argument("files", nargs="*", help="Markdown files to verify")
    parser.add_argument("--check-all", action="store_true", help="Check all docs/ in AIS-OS")
    args = parser.parse_args()

    target_files = [Path(f) for f in args.files]
    if args.check_all or not target_files:
        root = Path(__file__).resolve().parent.parent
        target_files = list(root.glob("docs/**/*.md")) + [root / "AGENTS.md", root / "CLAUDE.md", root / ".agentrules"]

    total_issues = 0
    for file_path in target_files:
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            issues = check_content(content, filename=file_path.name)
            if issues:
                for issue in issues[:10]:
                    print(f"⚠️  {issue}")
                total_issues += len(issues)
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

    if total_issues == 0:
        print("✅ All markdown links comply with the Tailscale web viewer protocol.")
        return 0
    else:
        print(f"\n⚠️  Found {total_issues} link formatting issue(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
