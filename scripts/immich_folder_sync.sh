#!/usr/bin/env bash
# Synchronize folder structure from /home/achibukz/Documents/Files/personal/memories into Immich albums.
set -euo pipefail

IMMICH_API_KEY="${IMMICH_API_KEY:-wg7HXbSpxBULbYNW9SGHuHWFwLIIDxzNclScCJjI}"
MEMORIES_PATH="/home/achibukz/Documents/Files/personal/memories"
CONTAINER_NETWORK="big-bear-immich_big_bear_immich_network"
API_URL="http://immich-server:2283/api"
ROOT_PATH="/mnt/media/memories"

EXTRA_ARGS=()
if [ "${1:-}" = "--dry-run" ] || [ "${1:-}" = "-d" ]; then
  EXTRA_ARGS+=("--dry-run")
fi

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
