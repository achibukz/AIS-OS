#!/usr/bin/env bash
# Synchronize folder structure from every Memories external-library root into Immich albums.
set -euo pipefail

IMMICH_API_KEY="${IMMICH_API_KEY:-wg7HXbSpxBULbYNW9SGHuHWFwLIIDxzNclScCJjI}"
CONTAINER_NETWORK="big-bear-immich_big_bear_immich_network"
API_URL="http://immich-server:2283/api"
LOCAL_API_URL="http://127.0.0.1:2283/api"

# Each source must be mounted at the same path Immich stores for its assets.
SYNC_SOURCES=(
  "/home/achibukz/Documents/Files/personal/memories:/mnt/media/memories"
  "/mnt/Achi120/Main Folders/Pictures/Memories 2:/mnt/media/memories2"
)

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

for sync_source in "${SYNC_SOURCES[@]}"; do
  source_path="${sync_source%%:*}"
  root_path="${sync_source#*:}"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running folder-to-album sync for ${root_path}..."
  docker run --rm \
    --network "${CONTAINER_NETWORK}" \
    -v "${source_path}:${root_path}:ro" \
    -e API_URL="${API_URL}" \
    -e API_KEY="${IMMICH_API_KEY}" \
    -e ROOT_PATH="${root_path}" \
    -e ALBUM_LEVELS=1 \
    -e UNATTENDED=1 \
    salvoxia/immich-folder-album-creator:latest \
    "${EXTRA_ARGS[@]}"
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync completed successfully."
