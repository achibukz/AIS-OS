import re
from datetime import date
from pathlib import Path

SEGMENT_RE = re.compile(
    r"^\[(\d{2}):(\d{2}):(\d{2})\.\d{3} --> (\d{2}):(\d{2}):(\d{2})\.\d{3}\]\s*(.*)$"
)


def parse_segment(line: str):
    m = SEGMENT_RE.match(line.strip())
    if not m:
        return None
    h1, m1, s1, h2, m2, s2, text = m.groups()
    start = int(h1) * 3600 + int(m1) * 60 + int(s1)
    end = int(h2) * 3600 + int(m2) * 60 + int(s2)
    return start, end, text.strip()


def format_timestamp(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def slugify(stem: str) -> str:
    slug = re.sub(r"[^\w\-]+", "-", stem).strip("-").lower()
    return slug or "untitled"


def output_path(outputs_dir: Path, source_name: str, on: date | None = None) -> Path:
    on = on or date.today()
    base = f"{on:%Y-%m-%d}-{slugify(Path(source_name).stem)}"
    candidate = outputs_dir / f"{base}.md"
    n = 2
    while candidate.exists():
        candidate = outputs_dir / f"{base}-{n}.md"
        n += 1
    return candidate


def group_segments(segments: list[tuple[int, int, str]], window: int = 60) -> str:
    paragraphs = []
    current: list[str] = []
    para_start = None
    prev_text = None
    for start, _end, text in segments:
        if not text or text == prev_text:
            continue
        prev_text = text
        if para_start is None:
            para_start = start
        elif start - para_start >= window:
            paragraphs.append(f"[{format_timestamp(para_start)}] " + " ".join(current))
            current = []
            para_start = start
        current.append(text)
    if current:
        paragraphs.append(f"[{format_timestamp(para_start)}] " + " ".join(current))
    return "\n\n".join(paragraphs)


def render_markdown(source_name: str, duration: float, body: str, on: date | None = None) -> str:
    on = on or date.today()
    return (
        f"# {Path(source_name).stem}\n\n"
        f"- Source: {source_name}\n"
        f"- Transcribed: {on:%Y-%m-%d}\n"
        f"- Duration: {format_timestamp(int(duration))}\n\n"
        f"{body}\n"
    )
