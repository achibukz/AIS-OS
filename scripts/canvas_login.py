#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp>=3.12,<4", "requests>=2.32,<3"]
# ///
"""Open a temporary, operator-only Canvas browser over Tailscale."""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import os
import signal
import ssl
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from aiohttp import ClientError, ClientSession, ClientTimeout, WSMsgType, web

from canvas_client import CONFIG, CanvasError, atomic_write
from canvas_reauth import replace_session

IMAGE = "lscr.io/linuxserver/chromium@sha256:27f41698ae1e6193c54f8d0176f9049d3620b3d4bd6bf4eb600dc2577d76d7af"
PAGE = """<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canvas login</title><style>
html,body{height:100%;margin:0}body{font:16px system-ui;display:flex;flex-direction:column;height:100dvh}
header{padding:8px 12px;background:#fff}h1{font-size:18px;margin:0}p{margin:6px 0}
nav{display:flex;gap:8px}button{font:inherit;padding:8px}iframe{flex:1;width:100%;border:0;min-height:0}
</style><header><h1>Canvas login</h1><p>Sign in below, then verify. This browser runs on Ubuntu.</p>
<nav><button id="verify">Verify and save</button><button id="cancel">Cancel login</button></nav>
<p id="result" role="status"></p></header>
<iframe title="Ubuntu Canvas browser" src="/desktop" allow="fullscreen"></iframe><script>
let completed=false;const buttons=[...document.querySelectorAll('button')];
for (const action of ['verify','cancel']) document.getElementById(action).onclick=async()=>{
if(completed)return;for(const button of buttons)button.disabled=true;
try{const response=await fetch('/canvas/'+action,{method:'POST',headers:{'X-Canvas-Action':'1'}});
const data=await response.json();completed=data.authentication==='valid'||data.status==='Login cancelled';
if(completed)document.querySelector('iframe').remove();
document.getElementById('result').textContent=
data.authentication==='valid'?'Canvas session saved. You can close this page.':data.error||data.status;
}catch(e){document.getElementById('result').textContent='Login window closed or connection lost.';}
finally{for(const button of buttons)button.disabled=completed;}};</script>"""

# This runs inside the temporary browser. Only Canvas cookies leave the container.
EXPORT = """
import asyncio, json
from aiohttp import ClientError, ClientSession, ClientTimeout
async def main():
    async with ClientSession(timeout=ClientTimeout(total=10)) as client:
        async with client.get('http://127.0.0.1:9222/json/version') as response:
            endpoint = (await response.json())['webSocketDebuggerUrl']
        async with client.ws_connect(endpoint) as ws:
            await ws.send_json({'id':1,'method':'Storage.getCookies'})
            result = await ws.receive_json()
            while result.get('id') != 1:
                result = await ws.receive_json()
            rows = result['result']['cookies']
            print(json.dumps([r for r in rows if r.get('domain') in
                  ('dlsu.instructure.com','.dlsu.instructure.com') and 'partitionKey' not in r]))
asyncio.run(main())
"""


def command(args, timeout=30):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        raise CanvasError("browser_command_failed") from None


def tailnet_owner(listen: str) -> int:
    status = json.loads(command(["tailscale", "status", "--json"]))
    own = status.get("Self", {})
    if listen not in own.get("TailscaleIPs", []) or type(own.get("UserID")) is not int:
        raise CanvasError("listen_must_be_own_tailscale_address")
    return own["UserID"]


def tls_configuration(config: Path):
    status = json.loads(command(["tailscale", "status", "--json"]))
    hostname = status["Self"]["DNSName"].rstrip(".")
    directory = config / "tls"
    key = directory / "server.key"
    if key.is_symlink() or key.stat().st_uid != os.getuid() or key.stat().st_mode & 0o077:
        raise CanvasError("unsafe_tls_key")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(directory / "server.crt", key)
    return hostname, context


async def identify(peer: str) -> dict:
    try:
        ipaddress.ip_address(peer)
        data = await asyncio.to_thread(command, ["tailscale", "whois", "--json", peer], 5)
        return json.loads(data)
    except (ValueError, CanvasError):
        return {}


class Browser:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.name = "achios-canvas-login-" + uuid.uuid4().hex
        self.unit = self.name + ".service"

    def start(self) -> str:
        args = ["systemd-run", "--user", "--quiet", "--collect", "--unit=" + self.unit,
                "--property=RuntimeMaxSec=" + str(self.seconds),
                "--property=TimeoutStopSec=15", "--property=StandardOutput=null",
                "--property=StandardError=null",
                "--property=ExecStopPost=/usr/bin/docker rm -f " + self.name,
                "/usr/bin/docker", "run", "--rm", "--name", self.name,
                "--label", "achios.canvas-login=true", "--log-driver=none",
                "--publish", "127.0.0.1::3000", "--shm-size=512m",
                "--tmpfs", "/config:rw,nosuid,nodev,size=512m",
                "--env", "PUID=" + str(os.getuid()), "--env", "PGID=" + str(os.getgid()),
                "--env", "HARDEN_DESKTOP=true", "--env", "SELKIES_ENABLE_SHARING=false",
                "--env", "SELKIES_CLIPBOARD_ENABLED=false|locked",
                "--env", "SELKIES_AUDIO_ENABLED=false|locked",
                "--env", "SELKIES_MICROPHONE_ENABLED=false|locked",
                "--env", "SELKIES_MANUAL_WIDTH=1024", "--env", "SELKIES_MANUAL_HEIGHT=768",
                "--env", "CHROME_CLI=--remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 "
                         "--user-data-dir=/config/canvas-profile --no-first-run https://dlsu.instructure.com",
                IMAGE]
        command(args)
        until = time.monotonic() + min(60, self.seconds)
        while time.monotonic() < until:
            try:
                binding = command(["docker", "port", self.name, "3000/tcp"]).strip()
                if binding.startswith("127.0.0.1:") and binding.split(":")[1].isdigit():
                    return "http://" + binding
            except CanvasError:
                pass
            time.sleep(.5)
        raise CanvasError("browser_start_timeout")

    def cookies(self) -> list[dict]:
        data = command(["docker", "exec", self.name, "/lsiopy/bin/python3", "-c", EXPORT], timeout=15)
        try:
            rows = json.loads(data)
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError
            return rows
        except ValueError:
            raise CanvasError("browser_export_failed") from None

    def close(self):
        try:
            command(["systemctl", "--user", "stop", self.unit])
        except CanvasError:
            remaining = command(["docker", "ps", "-aq", "--filter", "name=^/" + self.name + "$"])
            if remaining.strip():
                raise CanvasError("browser_cleanup_failed") from None


class Login:
    def __init__(self, origin: str, operator: int, upstream: str, browser: Browser,
                 config: Path, deadline: float):
        self.origin, self.operator, self.upstream = origin, operator, upstream
        self.browser, self.config = browser, config
        self.deadline = deadline
        self.finished = asyncio.Event()
        self.verifying = False
        self.result = None
        self.sockets = set()

    @web.middleware
    async def authorize(self, request, handler):
        if self.finished.is_set() or time.monotonic() >= self.deadline:
            raise web.HTTPGone(text="Login window closed")
        if request.host != urlsplit(self.origin).netloc:
            raise web.HTTPForbidden(text="Access denied")
        identity = await identify(request.remote or "")
        if (identity.get("UserProfile", {}).get("ID") != self.operator
                or identity.get("Node", {}).get("Tags")):
            raise web.HTTPForbidden(text="Access denied")
        origin = request.headers.get("Origin")
        if origin is not None and origin != self.origin:
            raise web.HTTPForbidden(text="Access denied")
        navigating = request.method == "GET" and request.headers.get("Sec-Fetch-Mode") == "navigate"
        if not navigating and request.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
            raise web.HTTPForbidden(text="Access denied")
        if request.method != "GET" or request.headers.get("Upgrade", "").lower() == "websocket":
            if origin != self.origin:
                raise web.HTTPForbidden(text="Access denied")
        return await handler(request)

    async def controls(self, request):
        if request.method == "GET" and request.path in ("/", "/canvas"):
            return web.Response(text=PAGE, content_type="text/html")
        if request.method != "POST" or request.headers.get("X-Canvas-Action") != "1" or request.can_read_body:
            raise web.HTTPBadRequest(text="Invalid operation")
        if request.path == "/canvas/cancel":
            if self.verifying:
                return web.json_response({"error": "verification_in_progress"}, status=409)
            self.finished.set()
            return web.json_response({"status": "Login cancelled"})
        if request.path != "/canvas/verify":
            raise web.HTTPNotFound()
        if self.verifying:
            return web.json_response({"error": "verification_in_progress"}, status=409)
        self.verifying = True
        try:
            rows = await asyncio.to_thread(self.browser.cookies)
            if time.monotonic() >= self.deadline:
                raise CanvasError("login_expired")
            result = await asyncio.to_thread(replace_session, rows, self.config, deadline=self.deadline)
            self.result = result
            self.finished.set()
            return web.json_response(result)
        except CanvasError as exc:
            return web.json_response({"error": exc.kind}, status=409)
        except (OSError, ValueError, KeyError):
            return web.json_response({"error": "session_save_failed"}, status=500)
        finally:
            self.verifying = False

    async def proxy(self, request):
        if request.method != "GET" or not request.raw_path.startswith("/") or request.raw_path.startswith("//"):
            raise web.HTTPForbidden()
        target = self.upstream + ("/" if request.path == "/desktop" else request.raw_path)
        try:
            if request.headers.get("Upgrade", "").lower() == "websocket":
                async with self.client.ws_connect(target, origin=self.origin, max_msg_size=16*1024*1024) as upstream:
                    downstream = web.WebSocketResponse(max_msg_size=16*1024*1024)
                    await downstream.prepare(request)
                    self.sockets.add(downstream)
                    async def relay(source, destination):
                        async for message in source:
                            if message.type == WSMsgType.BINARY:
                                await destination.send_bytes(message.data)
                            elif message.type == WSMsgType.TEXT:
                                await destination.send_str(message.data)
                            else:
                                break
                    tasks = [asyncio.create_task(relay(downstream, upstream)),
                             asyncio.create_task(relay(upstream, downstream))]
                    try:
                        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    finally:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        await downstream.close()
                        self.sockets.discard(downstream)
                    return downstream
            async with self.client.get(target, allow_redirects=False) as response:
                headers = {key: value for key, value in response.headers.items()
                           if key.lower() in ("content-type", "content-encoding", "location")}
                return web.Response(body=await response.read(), status=response.status, headers=headers)
        except (ClientError, OSError, asyncio.TimeoutError):
            raise web.HTTPBadGateway(text="Browser unavailable") from None

    def app(self):
        app = web.Application(middlewares=[self.authorize], client_max_size=1024)
        app.router.add_route("*", "/", self.controls)
        app.router.add_route("*", "/canvas", self.controls)
        app.router.add_route("*", "/canvas/{action}", self.controls)
        app.router.add_route("*", "/{path:.*}", self.proxy)
        async def headers(request, response):
            response.headers.update({"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                                     "X-Frame-Options": "SAMEORIGIN", "X-Content-Type-Options": "nosniff"})
        async def clients(app):
            async with ClientSession(timeout=ClientTimeout(total=30), auto_decompress=False) as client:
                self.client = client
                yield
        async def shutdown(app):
            for ws in list(self.sockets):
                await ws.close()
        app.on_shutdown.append(shutdown)
        app.on_response_prepare.append(headers)
        app.cleanup_ctx.append(clients)
        return app


async def serve(args):
    owner = tailnet_owner(args.listen)
    if owner != args.operator_id:
        raise CanvasError("operator_must_own_tailscale_host")
    hostname, tls = tls_configuration(args.config)
    browser = Browser(args.seconds)
    runner = None
    deadline = time.monotonic() + args.seconds
    try:
        upstream = await asyncio.to_thread(browser.start)
        origin = f"{'https' if tls else 'http'}://{hostname}:{args.port}"
        login = Login(origin, owner, upstream, browser, args.config, deadline)
        runner = web.AppRunner(login.app(), access_log=None, shutdown_timeout=5)
        await runner.setup()
        await web.TCPSite(runner, args.listen, args.port, ssl_context=tls).start()
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_running_loop().add_signal_handler(sig, login.finished.set)
        print(json.dumps({"login_url": origin + "/canvas", "expires_in_seconds": max(0, int(deadline - time.monotonic())),
                          "container": browser.name}), flush=True)
        try:
            await asyncio.wait_for(login.finished.wait(), timeout=max(0, deadline - time.monotonic()))
        except asyncio.TimeoutError:
            pass
        # Let an in-flight bounded probe finish before closing its browser or config.
        while login.verifying:
            await asyncio.sleep(.1)
        if login.result:
            atomic_write(args.config / "reauth-receipt.json", json.dumps(login.result))
            print(json.dumps(login.result), flush=True)
    finally:
        if runner:
            await runner.cleanup()
        await asyncio.to_thread(browser.close)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen", required=True, help="This host's Tailscale IPv4 address")
    parser.add_argument("--operator-id", required=True, type=int, help="Operator's numeric Tailscale user ID")
    parser.add_argument("--port", type=int, default=8769)
    parser.add_argument("--seconds", type=int, default=1200)
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args(argv)
    if not 1 <= args.seconds <= 1200 or not 1024 <= args.port <= 65535:
        parser.error("seconds must be 1..1200 and port 1024..65535")
    try:
        asyncio.run(serve(args))
    except (CanvasError, OSError, ValueError) as exc:
        print(json.dumps({"error": exc.kind if isinstance(exc, CanvasError) else "login_unavailable"}), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
