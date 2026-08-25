import re
from datetime import date
from pathlib import Path

import yt_dlp

SEGMENT_RE = re.compile(
    r"^\[(\d{2}):(\d{2}):(\d{2})\.\d{3} --> (\d{2}):(\d{2}):(\d{2})\.\d{3}\]\s*(.*)$"
)

ERROR_RE = re.compile(r"error|failed", re.IGNORECASE)

YOUTUBE_RE = re.compile(
    r"^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?.*v=|shorts/|embed/)|youtu\.be/)([\w\-]+)(\S*)?$",
    re.IGNORECASE,
)


def is_youtube_url(text: str) -> bool:
    if not text:
        return False
    return bool(YOUTUBE_RE.match(text.strip()))


def fetch_youtube_metadata(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url.strip(), download=False)
        return {
            "title": info.get("title") or "YouTube Video",
            "duration": float(info.get("duration") or 0.0),
            "uploader": info.get("uploader") or info.get("channel") or "",
        }


def download_youtube_audio(url: str, output_dir: Path, jid: str) -> tuple[Path, dict]:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / f"{jid}-%(title).80s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url.strip(), download=True)
        filename = ydl.prepare_filename(info)
        path = Path(filename)
        if not path.exists():
            matches = list(output_dir.glob(f"{jid}-*"))
            if matches:
                path = matches[0]
        meta = {
            "title": info.get("title") or "YouTube Video",
            "duration": float(info.get("duration") or 0.0),
            "uploader": info.get("uploader") or info.get("channel") or "",
        }
        return path, meta


def whisper_error(log: str) -> str:
    lines = [line.strip() for line in log.splitlines() if line.strip()]
    for line in lines:
        if ERROR_RE.search(line):
            return line
    return lines[-1] if lines else "whisper.cpp exited with an error"


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
    outputs_dir.mkdir(parents=True, exist_ok=True)
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


def render_markdown(
    source_name: str,
    duration: float,
    body: str,
    on: date | None = None,
    url: str | None = None,
    channel: str | None = None,
) -> str:
    on = on or date.today()
    title = Path(source_name).stem if not url else source_name
    lines = [f"# {title}\n"]
    if url:
        lines.append(f"- Source: {url}")
        if channel:
            lines.append(f"- Channel: {channel}")
    else:
        lines.append(f"- Source: {source_name}")
    lines.append(f"- Transcribed: {on:%Y-%m-%d}")
    lines.append(f"- Duration: {format_timestamp(int(duration))}\n")
    lines.append(body + "\n")
    return "\n".join(lines)
