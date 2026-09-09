# Canvas phone login

Issue [#27](https://github.com/achibukz/AIS-OS/issues/27) adds a temporary Ubuntu browser for operator login. Phone Google login with the Mac closed and authenticated Ubuntu session replacement passed on 2026-09-09. Adding these scripts does not deploy scheduled sync or schoolMem integration.

## Start a login window

Enable HTTPS Certificates in the Tailscale DNS admin page first. MagicDNS alone is insufficient. If `tailscale cert` reports that the account does not support TLS certificates, keep the login gate closed and enable that prerequisite. Certificate hostnames appear in public certificate-transparency logs; this does not publish the service.

Run from the achiOS checkout as the coordinator's Unix user, with Docker, the systemd user manager, Tailscale and uv available. Pull the browser image before opening a window. The script's inline dependency declaration installs aiohttp and requests through uv.

```bash
docker pull lscr.io/linuxserver/chromium@sha256:27f41698ae1e6193c54f8d0176f9049d3620b3d4bd6bf4eb600dc2577d76d7af
mkdir -p -m 700 ~/.config/achios/canvas/tls
sudo tailscale cert --cert-file ~/.config/achios/canvas/tls/server.crt --key-file ~/.config/achios/canvas/tls/server.key achibuntu.tail6e5ca1.ts.net
sudo chown achibukz:achibukz ~/.config/achios/canvas/tls/server.crt ~/.config/achios/canvas/tls/server.key
uv run scripts/canvas_login.py --listen 100.106.210.38 --operator-id 5281411258996113
```

The numeric operator ID must own the selected Tailscale address. Check the host's current identity with `tailscale status --json` before using this command on another machine. No secret belongs in a command argument. Certificate issuance may require an interactive administrator step. The gateway checks private-key ownership and permissions and refuses to start without its TLS files. Renew the certificate through the same command before it expires.

Open the emitted `/canvas` link in Safari or Chrome on a phone connected to Tailscale. The Ubuntu browser appears below the controls on the same page. Sign in to Canvas with Google and complete MFA yourself, then select Verify and save above the browser. The root URL also shows these controls, so reopening the link cannot strand you in a separate desktop tab. A successful response means the Ubuntu HTTP client received a valid profile from Canvas and committed the new cookies. A Canvas page appearing in the browser alone does not establish this.

The default window lasts at most 20 minutes including browser startup. `--seconds` can shorten it. Cancel, successful verification, a termination signal or expiry closes the gateway and stops its temporary browser. Starting again creates a clean profile and a new window. The URL contains no session or access credential and cannot reopen an expired window.

## Access and cleanup

Infrastructure inspection found an existing LinuxServer Obsidian desktop using Selkies, with both vaults mounted. It is left alone. The login uses LinuxServer's Chromium/Selkies image in a separate container with no host directory or Docker-socket mounts. Its `/config` profile is tmpfs. The Chromium debugging port stays inside the container and is never published.

Only the gateway binds the host's Tailscale address. It resolves each connection's actual peer through `tailscale whois` and checks the operator's numeric user ID. Tagged nodes, unknown identities, mismatched Host, foreign Origin and cross-site control requests are denied. Forwarded identity headers cannot authenticate a request. WebSocket upgrades receive the same checks. HTTPS uses the host's Tailscale DNS name, which lets the phone use WebCodecs. Tailscale also encrypts the network path. The host's local processes and Docker administrators remain trusted.

The desktop backend publishes one random loopback port. A transient systemd user unit owns the container with `RuntimeMaxSec` and `ExecStopPost`. This expires the browser even if the Python gateway crashes. The container has no restart policy and uses `--rm`; its browser profile disappears on removal. Browser output, Docker logs and gateway access logs are disabled. Clipboard sync, file transfer, command execution and desktop sharing are disabled.

For a gateway process that was killed, the emitted container name also names the transient unit. Stop only that owned unit if immediate cleanup is needed:

```bash
systemctl --user stop achios-canvas-login-<run-id>.service
```

Do not stop Obsidian or unrelated units. Verify the matching container no longer exists with `docker ps -a --filter name=achios-canvas-login-<run-id>`.

## Session replacement

Only cookies scoped exactly to `dlsu.instructure.com` or `.dlsu.instructure.com` leave the temporary browser. Google cookies, parent-domain cookies, unrelated subdomains and partitioned cookies are excluded. Host/domain scope, path, Secure, HttpOnly and expiry are retained. The full browser profile is never copied to the host.

Replacement takes the existing Canvas writer lock shared by sync, mapping and delivery. A busy lock returns `busy` without writing a candidate. A private temporary candidate store runs the existing GET-only client's profile probe, with its origin, redirect and timeout restrictions. If a verified course mapping exists, its Canvas user ID must match the profile. Only after that check succeeds, and before the login deadline, does atomic replacement update `cookies.txt`. An expired window, wrong account, failed network request or failed rename preserves the saved jar. Response cookie rotations from the successful probe are included.

The result and private `reauth-receipt.json` contain only authentication status and a check timestamp. Reauthentication does not refresh cached facts or their timestamps, and it sends no notification. The next explicit probe or sync records the cache's authentication transition through the existing path.

A worker cannot use this command to bypass the coordinator's write boundary. Issue #173 still owns the validated schoolMem control path. Do not expose the Docker socket, arbitrary config paths or shell arguments to a bound worker.

## Live acceptance on 2026-09-09

The operator reached Canvas through the Ubuntu browser on his phone and explicitly confirmed his Mac was closed. The first two-tab layout made the Verify control difficult to recover. The coordinator invoked the same Verify endpoint, which returned valid authentication at 05:45:19 UTC and saved the candidate. A second client probe at 05:46:22 UTC succeeded after the temporary browser was removed and matched the mapped account. This proves session transfer and browser-independent access; it does not establish session lifetime.

The revised layout keeps the browser and controls on one page. Both the root URL and `/canvas` open it. An automated mobile viewport check found the Verify button visible above a working desktop stream. The interaction record retains the earlier navigation failure and distinguishes coordinator verification from a phone button press. A second successful Verify closed the revised window before the reported Cancel attempt. Completed pages now disable both buttons and remove the desktop frame, preserving the final message. A live browser click returned Login cancelled, disabled both controls and removed the temporary container; a simulated success response separately verified the saved-session message behavior.

## Verification

```bash
uv run --with pytest --with requests --with aiohttp python -m pytest tests/ -q
```

The final full-suite run returned 452 passed in 33.88s. Automated tests exercise access denial, WebSocket origin checks, expiry, duplicate verification, cleanup configuration, cookie scope, wrong accounts, lock contention and failed replacement. Assisted acceptance must separately establish Google/MFA from the phone with the Mac closed, a valid Ubuntu API response afterward and actual container cleanup. If Google rejects the browser, keep #27 open and record the failure before trying another browser.

Sources: [LinuxServer Chromium](https://docs.linuxserver.io/images/docker-chromium/) documents Selkies, its loopback proxy requirement and desktop controls. [Tailscale CLI](https://tailscale.com/docs/reference/tailscale-cli) documents peer identity lookup.
