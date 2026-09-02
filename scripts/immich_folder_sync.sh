#!/usr/bin/env bash
# Synchronize folder structure from /home/achibukz/Documents/Files/personal/memories into Immich albums.
set -euo pipefail

IMMICH_API_KEY="${IMMICH_API_KEY:-wg7HXbSpxBULbYNW9SGHuHWFwLIIDxzNclScCJjI}"
MEMORIES_PATH="/home/achibukz/Documents/Files/personal/memories"
CONTAINER_NETWORK="big-bear-immich_big_bear_immich_network"
API_URL="http://immich-server:2283/api"
LOCAL_API_URL="http://127.0.0.1:2283/api"
ROOT_PATH="/mnt/media/memories"

EXTRA_ARGS=()
IS_DRY_RUN=0
if [ "${1:-}" = "--dry-run" ] || [ "${1:-}" = "-d" ]; then
  EXTRA_ARGS+=("--dry-run")
  IS_DRY_RUN=1
fi

if [ "$IS_DRY_RUN" -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Triggering Immich external library scan..."
  curl -s -f -X POST -H "x-api-key: ${IMMICH_API_KEY}" "${LOCAL_API_URL}/libraries/a2a09d4e-cbc0-4268-ac14-27b50be20c22/scan" || true
  sleep 5
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running folder-to-album sync..."
docker run --rm \
  --network "${CONTAINER_NETWORK}" \
  -v "${MEMORIES_PATH}:${ROOT_PATH}:ro" \
  -e API_URL="${API_URL}" \
  -e API_KEY="${IMMICH_API_KEY}" \
  -e ROOT_PATH="${ROOT_PATH}" \
  -e ALBUM_LEVELS=1 \
  -e UNATTENDED=1 \
  salvoxia/immich-folder-album-creator:latest \
  "${EXTRA_ARGS[@]}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync completed successfully."
