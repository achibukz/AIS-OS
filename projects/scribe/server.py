import asyncio
import json
import queue
import shutil
import subprocess
import threading
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from core import group_segments, output_path, parse_segment, render_markdown, whisper_error

ROOT = Path(__file__).parent
UPLOADS = ROOT / "uploads"
OUTPUTS = ROOT / "outputs"
MODEL = ROOT / "models" / "ggml-large-v3-turbo.bin"

app = FastAPI()

jobs: dict[str, dict] = {}
job_order: list[str] = []
work_queue: queue.Queue[str] = queue.Queue()
listeners: list[asyncio.Queue] = []
loop: asyncio.AbstractEventLoop | None = None


def whisper_binary() -> str:
    for name in ("whisper-cli", "whisper-cpp"):
        if shutil.which(name):
            return name
    raise RuntimeError("whisper.cpp not found — brew install whisper-cpp")


def snapshot() -> list[dict]:
    return [
        {k: v for k, v in jobs[jid].items() if k != "upload_path"}
        for jid in job_order
    ]


def broadcast():
    if loop is None:
        return
    data = snapshot()
    for q in list(listeners):
        loop.call_soon_threadsafe(q.put_nowait, data)


def update(jid: str, **fields):
    jobs[jid].update(fields)
    broadcast()


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def transcribe(jid: str):
    job = jobs[jid]
    src = Path(job["upload_path"])
    wav = src.with_suffix(".16k.wav")
    errlog = src.with_suffix(".err.log")
    try:
        update(jid, status="extracting")
        duration = probe_duration(src)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src),
             "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
            check=True, capture_output=True,
        )

        update(jid, status="transcribing", duration=duration)
        with errlog.open("w") as err:
            proc = subprocess.Popen(
                [whisper_binary(), "-m", str(MODEL), "-l", "auto", "-mc", "0", "-f", str(wav)],
                stdout=subprocess.PIPE, stderr=err, text=True,
            )
            segments = []
            for line in proc.stdout:
                seg = parse_segment(line)
                if seg:
                    segments.append(seg)
                    update(jid, progress=min(seg[1] / duration, 1.0) if duration else 0)
            if proc.wait() != 0:
                raise RuntimeError(whisper_error(errlog.read_text()))
        if not segments:
            raise RuntimeError("no speech found in file")

        dest = output_path(OUTPUTS, job["name"])
        dest.write_text(render_markdown(job["name"], duration, group_segments(segments)))
        src.unlink(missing_ok=True)
        update(jid, status="done", progress=1.0, output=dest.name)
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        update(jid, status="error", error=detail.strip().splitlines()[-1] if detail.strip() else "ffmpeg failed")
    except Exception as e:
        update(jid, status="error", error=str(e))
    finally:
        wav.unlink(missing_ok=True)
        errlog.unlink(missing_ok=True)


def worker():
    while True:
        transcribe(work_queue.get())


@app.on_event("startup")
async def startup():
    global loop
    loop = asyncio.get_running_loop()
    UPLOADS.mkdir(exist_ok=True)
    OUTPUTS.mkdir(exist_ok=True)
    threading.Thread(target=worker, daemon=True).start()


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.post("/api/jobs")
async def create_jobs(files: list[UploadFile]):
    created = []
    for f in files:
        jid = uuid.uuid4().hex[:8]
        dest = UPLOADS / f"{jid}-{Path(f.filename).name}"
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        jobs[jid] = {
            "id": jid, "name": Path(f.filename).name, "status": "queued",
            "progress": 0.0, "upload_path": str(dest),
        }
        job_order.append(jid)
        created.append(jid)
    broadcast()
    for jid in created:
        work_queue.put(jid)
    return snapshot()


@app.get("/api/events")
async def events():
    q: asyncio.Queue = asyncio.Queue()
    listeners.append(q)
    q.put_nowait(snapshot())

    async def stream():
        try:
            while True:
                data = await q.get()
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            listeners.remove(q)

    return StreamingResponse(stream(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8177)
