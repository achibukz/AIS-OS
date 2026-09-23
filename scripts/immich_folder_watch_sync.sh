#!/usr/bin/env bash
# Wait for a Memories transfer to settle, then scan and create its Immich album.
set -euo pipefail

WATCH_PATHS=(
  "/home/achibukz/Documents/Files/personal/memories"
  "/mnt/Achi120/Main Folders/Pictures/Memories 2"
)
QUIET_SECONDS="${QUIET_SECONDS:-120}"

for watch_path in "${WATCH_PATHS[@]}"; do
  if [ ! -d "$watch_path" ]; then
    echo "Memories root is unavailable at $watch_path" >&2
    exit 1
  fi
done

while true; do
  latest_epoch=0
  for watch_path in "${WATCH_PATHS[@]}"; do
    path_latest_epoch=$(find "$watch_path" -printf '%T@\n' | awk '$1 > max { max = $1 } END { printf "%.0f", max }')
    if [ "$path_latest_epoch" -gt "$latest_epoch" ]; then
      latest_epoch="$path_latest_epoch"
    fi
  done
  now_epoch=$(date +%s)

  if [ "$((now_epoch - latest_epoch))" -ge "$QUIET_SECONDS" ]; then
    break
  fi

  sleep 10
done

exec "$(dirname "$0")/immich_folder_sync.sh"
