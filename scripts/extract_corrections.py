#!/usr/bin/env python3
"""Autonomous Correction Harvester for achiOS.

Scans Obsidian vault tgdb dialogue sessions (achiMem/tgdb/YYYY-MM/*.md),
detects explicit user corrections, directives, banned words, and style preferences,
and updates .agentrules and decisions/log.md with zero duplicate entries.

Usage:
    python scripts/extract_corrections.py            # Harvest and apply corrections
    python scripts/extract_corrections.py --dry-run  # Preview detected corrections
    python scripts/extract_corrections.py --days 3   # Scan past N days (default: 2)
    python scripts/extract_corrections.py --file <path> # Scan specific file
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Manila")
DEFAULT_VAULT_PATH = Path.home() / "Documents" / "Obsidian" / "achiMem"
REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_RULES_PATH = REPO_ROOT / ".agentrules"
DECISIONS_LOG_PATH = REPO_ROOT / "decisions" / "log.md"
VOICE_REF_PATH = REPO_ROOT / "references" / "voice.md"


@dataclass
class HarvestedCorrection:
    source_file: Path
    date_str: str
    raw_quote: str
    trigger_type: str  # banned_word, directive, style, preference, factual
    rule_text: str
    domain: str  # voice, tasks, logging, policy, general


def clean_quote_text(text: str) -> str:
    """Strip blockquote markers, XML tags, and multiple spaces."""
    cleaned = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_corrections_from_text(content: str, source_path: Path) -> list[HarvestedCorrection]:
    """Parse dialogue text and identify user corrections using heuristic triggers."""
    corrections: list[HarvestedCorrection] = []

    # Extract date from YAML frontmatter or filename
    date_match = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", content, re.MULTILINE)
    if date_match:
        date_str = date_match.group(1)
    else:
        file_date = re.search(r"(\d{4}-\d{2}-\d{2})", source_path.name)
        date_str = file_date.group(1) if file_date else dt.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")

    # Extract dialogue blocks spoken by user (Aki)
    # Matches: > **Aki:** <text> or **Aki:** <text> until next speaker or block end
    user_blocks = re.findall(
        r"(?:^|\n)(?:>\s*)?\*\*Aki:\*\*\s*(.+?)(?=(?:\n(?:>\s*)?\*\*[^*]+:\*\*|\Z))",
        content,
        re.DOTALL,
    )

    for block in user_blocks:
        lines = [clean_quote_text(l) for l in block.splitlines() if clean_quote_text(l)]
        for line in lines:
            line_lower = line.lower()

            # 1. Banned words / Avoid terms
            banned_match = re.search(
                r"(?:can we not use|don'?t use|do not use|never use|stop using|avoid using|not use)\s+(?:the\s+word\s+)?[\"']?([a-zA-Z0-9_\-]+)[\"']?",
                line,
                re.IGNORECASE,
            )
            if banned_match:
                word = banned_match.group(1).strip().strip(".,;:?!")
                # Exclude system tools and common stop words
                if word and len(word) > 2 and word.lower() not in ("the", "this", "that", "it", "curl", "git", "bash", "python", "sudo", "grep"):
                    rule = f"Banned word / term: Never use '{word}' in generated correspondence or output."
                    corrections.append(
                        HarvestedCorrection(
                            source_file=source_path,
                            date_str=date_str,
                            raw_quote=line,
                            trigger_type="banned_word",
                            rule_text=rule,
                            domain="voice",
                        )
                    )
                    continue

            # 2. Tone & Formality adjustments
            if any(k in line_lower for k in ("less formal", "more casual", "make it less formal", "make it more casual", "too formal")):
                rule = f"Voice register adjustment: {line.strip()}"
                corrections.append(
                    HarvestedCorrection(
                        source_file=source_path,
                        date_str=date_str,
                        raw_quote=line,
                        trigger_type="style",
                        rule_text=rule,
                        domain="voice",
                    )
                )
                continue

            # 3. Directives & "Take note" / "Make sure"
            directive_match = re.search(
                r"(?:take note(?:\s+that|\s+on|\s*:|\s+of)?|make sure to|remember that|always make sure|rule:)\s*(.+)",
                line,
                re.IGNORECASE,
            )
            if directive_match and not line.strip().endswith("?"):
                raw_directive = directive_match.group(1).strip()
                # Clean leading prepositions
                raw_directive = re.sub(r"^(?:of\s+|that\s+|on\s+)", "", raw_directive, flags=re.IGNORECASE).strip()
                if len(raw_directive) > 8:
                    domain = "general"
                    if any(w in raw_directive.lower() for w in ("email", "voice", "draft", "say", "tone", "sign", "word", "message")):
                        domain = "voice"
                    elif any(w in raw_directive.lower() for w in ("task", "deadline", "priority", "todo", "cert", "clinic", "exam", "enroll", "schedule", "bank", "get", "buy", "order", "prepare")):
                        domain = "tasks"
                    elif any(w in raw_directive.lower() for w in ("log", "record", "commit", "sync", "push", "git")):
                        domain = "logging"

                    rule = f"Operational directive: {raw_directive[0].upper() + raw_directive[1:]}"
                    corrections.append(
                        HarvestedCorrection(
                            source_file=source_path,
                            date_str=date_str,
                            raw_quote=line,
                            trigger_type="directive",
                            rule_text=rule,
                            domain=domain,
                        )
                    )
                    continue


            # 4. Format / Replacement requests ("change X to Y")
            # Exclude questions like "how to change X to Y?"
            if not line.strip().endswith("?") and not line_lower.startswith(("how to", "is it", "can we")):
                change_match = re.search(
                    r"(?:change|update|replace)\s+(?:the\s+)?(.+?)\s+to\s+(.+)",
                    line,
                    re.IGNORECASE,
                )
                if change_match:
                    from_target = change_match.group(1).strip()
                    to_target = change_match.group(2).strip()
                    if len(from_target) > 2 and len(to_target) > 2:
                        rule = f"Formatting override: Change '{from_target}' to '{to_target}'"
                        domain = "voice" if any(w in line_lower for w in ("subject", "sign-off", "email", "name", "wording", "header")) else "general"
                        corrections.append(
                            HarvestedCorrection(
                                source_file=source_path,
                                date_str=date_str,
                                raw_quote=line,
                                trigger_type="preference",
                                rule_text=rule,
                                domain=domain,
                            )
                        )
                        continue


    return corrections


def is_rule_duplicate(rule_text: str, existing_corpus: str) -> bool:
    """Check if the extracted rule or its primary keyword is already present."""
    norm_rule = re.sub(r"[^\w\s]", "", rule_text.lower()).strip()
    norm_corpus = re.sub(r"[^\w\s]", "", existing_corpus.lower())

    # Direct phrase inclusion check
    if norm_rule in norm_corpus:
        return True

    # Check for banned word specifically
    banned_word_match = re.search(r"banned word\s*(?:/\s*term)?:\s*(?:never use\s*)?['\"]?([a-zA-Z0-9_\-]+)['\"]?", rule_text, re.IGNORECASE)
    if banned_word_match:
        banned_word = banned_word_match.group(1).lower()
        if banned_word in norm_corpus:
            return True

    return False


def get_existing_corpus() -> str:
    """Read all current rules and decision logs into a combined string for deduplication."""
    corpus_parts = []
    for path in (AGENT_RULES_PATH, DECISIONS_LOG_PATH, VOICE_REF_PATH):
        if path.exists():
            try:
                corpus_parts.append(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                pass
    return "\n\n".join(corpus_parts)


def apply_corrections(
    corrections: list[HarvestedCorrection],
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    """Deduplicate and apply harvested corrections to .agentrules and decisions/log.md."""
    existing_corpus = get_existing_corpus()
    applied_count = 0
    applied_summaries: list[str] = []

    new_decision_entries: list[str] = []
    new_agentrules_entries: list[str] = []

    for c in corrections:
        if is_rule_duplicate(c.rule_text, existing_corpus):
            continue

        applied_count += 1
        applied_summaries.append(f"[{c.date_str}] ({c.domain}) {c.rule_text}")

        # Update local memory corpus for subsequent items in the same run
        existing_corpus += f"\n{c.rule_text}\n{c.raw_quote}"

        # Prepare decision log entry
        decision_entry = f"""
## {c.date_str} — User Correction Harvested ({c.trigger_type})

**Decision:** {c.rule_text}

**Why:** Harvested from dialogue session `{c.source_file.name}`:
> "{c.raw_quote}"

**Domain:** `{c.domain}`
**Owner:** Aki.
"""
        new_decision_entries.append(decision_entry.strip())

        # Prepare .agentrules bullet
        new_agentrules_entries.append(f"- **{c.date_str} ({c.domain}):** {c.rule_text}")

    if dry_run or applied_count == 0:
        return applied_count, applied_summaries

    # 1. Append to decisions/log.md
    if new_decision_entries and DECISIONS_LOG_PATH.exists():
        current_decisions = DECISIONS_LOG_PATH.read_text(encoding="utf-8")
        updated_decisions = current_decisions.rstrip() + "\n\n" + "\n\n".join(new_decision_entries) + "\n"
        DECISIONS_LOG_PATH.write_text(updated_decisions, encoding="utf-8")

    # 2. Append to .agentrules
    if new_agentrules_entries and AGENT_RULES_PATH.exists():
        current_rules = AGENT_RULES_PATH.read_text(encoding="utf-8")
        header = "\n## 5. Harvested User Preferences & Corrections\n"
        if header not in current_rules:
            updated_rules = current_rules.rstrip() + "\n" + header + "\n".join(new_agentrules_entries) + "\n"
        else:
            updated_rules = current_rules.rstrip() + "\n" + "\n".join(new_agentrules_entries) + "\n"
        AGENT_RULES_PATH.write_text(updated_rules, encoding="utf-8")

    return applied_count, applied_summaries


def scan_vault_tgdb(
    vault_path: Path = DEFAULT_VAULT_PATH,
    days_lookback: int = 2,
    single_file: Path | None = None,
) -> list[HarvestedCorrection]:
    """Scan tgdb markdown files and extract all corrections."""
    corrections: list[HarvestedCorrection] = []

    if single_file:
        if single_file.exists():
            content = single_file.read_text(encoding="utf-8", errors="replace")
            corrections.extend(extract_corrections_from_text(content, single_file))
        return corrections

    tgdb_dir = vault_path / "tgdb"
    if not tgdb_dir.exists():
        return corrections

    now = dt.datetime.now(LOCAL_TZ)
    cutoff = now - dt.timedelta(days=days_lookback)

    # Find all monthly subdirectories
    for month_dir in sorted(tgdb_dir.iterdir()):
        if not month_dir.is_dir():
            continue
        for md_file in sorted(month_dir.glob("*.md")):
            try:
                mtime = dt.datetime.fromtimestamp(md_file.stat().st_mtime, tz=LOCAL_TZ)
                if mtime >= cutoff:
                    content = md_file.read_text(encoding="utf-8", errors="replace")
                    file_corrections = extract_corrections_from_text(content, md_file)
                    corrections.extend(file_corrections)
            except Exception as e:
                print(f"Error reading {md_file}: {e}", file=sys.stderr)

    return corrections


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest user corrections from tgdb session notes.")
    parser.add_argument("--dry-run", action="store_true", help="Preview detected corrections without writing")
    parser.add_argument("--days", type=int, default=2, help="Lookback window in days (default: 2)")
    parser.add_argument("--file", type=Path, default=None, help="Scan a specific Markdown file")
    parser.add_argument("--vault-dir", type=Path, default=DEFAULT_VAULT_PATH, help="Path to Obsidian vault")

    args = parser.parse_args()

    corrections = scan_vault_tgdb(
        vault_path=args.vault_dir,
        days_lookback=args.days,
        single_file=args.file,
    )

    if not corrections:
        print(f"No user correction triggers detected in tgdb across past {args.days} day(s).")
        return 0

    print(f"Detected {len(corrections)} potential correction item(s) from tgdb.")
    applied_count, summaries = apply_corrections(corrections, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n[DRY RUN] Would apply {applied_count} new unique correction(s):")
        for s in summaries:
            print(f"  • {s}")
    else:
        print(f"\nSuccessfully applied {applied_count} new unique correction(s) to .agentrules & decisions/log.md:")
        for s in summaries:
            print(f"  ✓ {s}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
