#!/usr/bin/env bash
# Fetch and fast-forward every git repo under the known roots.
set -uo pipefail

# Aki's own repos only. Third-party clones (~/.hermes/hermes-agent) and
# tool-managed ones (~/.claude plugin marketplaces) are not his to keep current.
DEFAULT_ROOTS=(
  "$HOME/Code/GitHub"
  "$HOME/Documents/Obsidian"
)

FETCH_TIMEOUT=${SYNC_REPOS_TIMEOUT:-300}

# A repo whose credentials went stale must fail, not sit waiting for a password.
export GIT_TERMINAL_PROMPT=0

roots=("$@")
if [ ${#roots[@]} -eq 0 ]; then
  roots=("${DEFAULT_ROOTS[@]}")
fi

repos=()
for root in "${roots[@]}"; do
  [ -d "$root" ] || continue
  while IFS= read -r gitdir; do
    repos+=("$(dirname "$gitdir")")
  done < <(find "$root" -maxdepth 4 -name .git -prune 2>/dev/null | sort)
done

if [ ${#repos[@]} -eq 0 ]; then
  echo "no repos found under: ${roots[*]}"
  exit 0
fi

width=0
for repo in "${repos[@]}"; do
  label=${repo#"$HOME"/}
  [ ${#label} -gt $width ] && width=${#label}
done

failures=0
warnings=0

for repo in "${repos[@]}"; do
  label=${repo#"$HOME"/}
  printf "%-${width}s  " "$label"

  if [ -z "$(git -C "$repo" remote)" ]; then
    echo "skipped       no remote"
    warnings=$((warnings + 1))
    continue
  fi

  err=$(timeout "$FETCH_TIMEOUT" git -C "$repo" fetch --all --prune --quiet 2>&1)
  code=$?
  if [ "$code" -ne 0 ]; then
    [ "$code" -eq 124 ] && err="timed out after ${FETCH_TIMEOUT}s"
    echo "FETCH FAILED  ${err//$'\n'/ }"
    failures=$((failures + 1))
    continue
  fi

  branch=$(git -C "$repo" symbolic-ref --short -q HEAD)
  if [ -z "$branch" ]; then
    echo "fetched       detached HEAD"
    warnings=$((warnings + 1))
    continue
  fi

  upstream=$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
  if [ -z "$upstream" ]; then
    echo "fetched       $branch has no upstream"
    warnings=$((warnings + 1))
    continue
  fi

  read -r behind ahead < <(git -C "$repo" rev-list --left-right --count "$upstream...HEAD")
  # Only tracked changes block a pull. A fast-forward leaves untracked files
  # alone, and aborts by itself if an incoming file would clobber one.
  dirty=$(git -C "$repo" status --porcelain --untracked-files=no | wc -l)
  untracked=$(git -C "$repo" ls-files --others --exclude-standard | wc -l)

  # A shallow clone's history is truncated, so almost everything upstream counts
  # as "behind". The fast-forward is still correct; only the number is nonsense.
  shallow=""
  [ "$(git -C "$repo" rev-parse --is-shallow-repository)" = "true" ] && shallow=" (shallow, count inflated)"

  if [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ]; then
    echo "DIVERGED      $branch is $behind behind, $ahead ahead of $upstream$shallow"
    failures=$((failures + 1))
    continue
  fi

  if [ "$behind" -gt 0 ] && [ "$dirty" -gt 0 ]; then
    echo "held back     $behind to pull, $dirty uncommitted change(s)$shallow"
    warnings=$((warnings + 1))
    continue
  fi

  if [ "$behind" -gt 0 ]; then
    if ! err=$(git -C "$repo" merge --ff-only --quiet "$upstream" 2>&1); then
      echo "PULL FAILED   ${err//$'\n'/ }"
      failures=$((failures + 1))
      continue
    fi
    status="pulled $behind"
  else
    status="up to date"
    shallow=""
  fi

  notes=""
  [ -n "$shallow" ] && notes="${shallow# }"
  [ "$ahead" -gt 0 ] && notes="${notes:+$notes, }$ahead unpushed"
  [ "$dirty" -gt 0 ] && notes="${notes:+$notes, }$dirty uncommitted"
  [ "$untracked" -gt 0 ] && notes="${notes:+$notes, }$untracked untracked"
  [ -n "$notes" ] && warnings=$((warnings + 1))
  printf "%-13s %s\n" "$status" "$notes"
done

echo
echo "${#repos[@]} repos, $failures failed, $warnings need a look"
[ "$failures" -gt 0 ] && exit 1
exit 0
