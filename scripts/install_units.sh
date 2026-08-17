#!/usr/bin/env bash
# Install achiOS systemd user timers from systemd/. Idempotent — re-run after editing a unit.
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
dest="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$dest" "$HOME/.local/state/achios"

for src in "$repo"/systemd/*.service "$repo"/systemd/*.timer; do
    sed "s|@REPO@|$repo|g" "$src" > "$dest/${src##*/}"
    echo "installed ${src##*/}"
done

systemctl --user daemon-reload

for timer in "$repo"/systemd/*.timer; do
    systemctl --user enable --now "${timer##*/}"
done

# Long-running services carry WantedBy=default.target so they come back after a reboot.
# The loop above only covers timers, and a service nothing activates would sit dead.
for svc in "$repo"/systemd/*.service; do
    if grep -q '^WantedBy=default.target' "$svc"; then
        systemctl --user enable --now "${svc##*/}"
    fi
done

# User timers stop firing when Aki logs out unless the user lingers.
loginctl enable-linger "$USER"

systemctl --user list-timers 'achios-*' --no-pager
