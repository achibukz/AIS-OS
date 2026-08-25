# scribe

Local audio/video & YouTube → text. Drag files in or paste YouTube links, get date-prefixed markdown transcripts in `outputs/`.

Whisper large-v3-turbo via whisper.cpp, Taglish-capable (`-l auto`). Sequential queue, real per-file progress, upload/download copies deleted after success.

## Requirements

- `brew install whisper-cpp ffmpeg`
- Model at `models/ggml-large-v3-turbo.bin` ([download](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin))

## Run

```sh
uv run server.py
```

Open http://127.0.0.1:8177

## Tests

```sh
uv run pytest
```
