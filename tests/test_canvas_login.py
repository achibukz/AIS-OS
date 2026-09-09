import asyncio
import json
import time
from types import SimpleNamespace

import pytest
from aiohttp import ClientSession, web, WSServerHandshakeError
from aiohttp.test_utils import TestServer

import canvas_login
from canvas_client import CanvasError


class Browser:
    def cookies(self):
        return []


def test_gateway_denies_unknown_identity_spoofed_headers_and_cross_site(tmp_path, monkeypatch):
    async def run():
        login = canvas_login.Login("http://login.test", 7, "http://127.0.0.1:1", Browser(), tmp_path, 1200)
        identity = {}
        async def identify(peer):
            assert peer == "127.0.0.1"
            return identity
        monkeypatch.setattr(canvas_login, "identify", identify)
        async with TestServer(login.app()) as server, ClientSession() as client:
            url = server.make_url('/canvas')
            response = await client.get(url, headers={"Host":"login.test", "Tailscale-User-Login":"operator", "X-Forwarded-For":"100.1.2.3"})
            assert response.status == 403
            identity.update({"UserProfile":{"ID":7}, "Node":{}})
            for headers in ({"Host":"evil.test"}, {"Host":"login.test", "Origin":"http://evil.test"},
                            {"Host":"login.test", "Sec-Fetch-Site":"cross-site"}):
                assert (await client.get(url, headers=headers)).status == 403
            assert (await client.post(server.make_url('/canvas/verify'), headers={"Host":"login.test"})).status == 403
            identity['Node']['Tags'] = ['tag:server']
            assert (await client.get(url, headers={"Host":"login.test"})).status == 403
            identity['Node'] = {}
            response = await client.get(url, headers={"Host":"login.test"})
            assert response.status == 200 and "Canvas login" in await response.text()
            assert response.headers['Cache-Control'] == 'no-store'
            login.deadline = time.monotonic() - 1
            assert (await client.get(url, headers={"Host":"login.test"})).status == 410
    asyncio.run(run())


def test_duplicate_verify_failed_retry_and_cancel(tmp_path, monkeypatch):
    async def run():
        login = canvas_login.Login("http://login.test", 7, "http://127.0.0.1:1", Browser(), tmp_path, 1200)
        async def identify(peer):
            return {"UserProfile":{"ID":7}}
        monkeypatch.setattr(canvas_login, "identify", identify)
        def failed(*args, **kwargs):
            raise CanvasError("authentication_expired")
        monkeypatch.setattr(canvas_login, "replace_session", failed)
        headers = {"Host":"login.test", "Origin":"http://login.test", "X-Canvas-Action":"1"}
        async with TestServer(login.app()) as server, ClientSession() as client:
            url = server.make_url('/canvas/verify')
            response = await client.post(url, headers=headers)
            assert (await response.json())['error'] == 'authentication_expired'
            assert not login.verifying and not login.finished.is_set()
            login.verifying = True
            for path in ('verify', 'cancel'):
                response = await client.post(server.make_url('/canvas/'+path), headers=headers)
                assert response.status == 409
                assert (await response.json())['error'] == 'verification_in_progress'
            login.verifying = False
            response = await client.post(url, data='arbitrary arguments', headers=headers)
            assert response.status == 400
            monkeypatch.setattr(canvas_login, 'replace_session', lambda *a, **k: {'authentication':'valid'})
            response = await client.post(url, headers=headers)
            assert (await response.json())['authentication'] == 'valid'
            assert login.finished.is_set()
            assert (await client.get(server.make_url('/canvas'), headers=headers)).status == 410
    asyncio.run(run())


def test_proxy_relays_websocket_only_after_identity_and_origin(tmp_path, monkeypatch):
    async def run():
        async def socket(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            async for message in ws:
                await ws.send_str(message.data)
            return ws
        upstream = web.Application()
        upstream.router.add_get('/socket', socket)
        async with TestServer(upstream) as backend:
            login = canvas_login.Login("http://login.test", 7, str(backend.make_url('')).rstrip('/'), Browser(), tmp_path, 1200)
            async def identify(peer):
                return {"UserProfile":{"ID":7}}
            monkeypatch.setattr(canvas_login, "identify", identify)
            async with TestServer(login.app()) as server, ClientSession() as client:
                with pytest.raises(WSServerHandshakeError) as error:
                    await client.ws_connect(server.make_url('/socket'), headers={'Host':'login.test'}, origin='http://evil.test')
                assert error.value.status == 403
                async with client.ws_connect(server.make_url('/socket'), headers={'Host':'login.test'}, origin='http://login.test') as ws:
                    await ws.send_str('test-input')
                    assert (await ws.receive()).data == 'test-input'
    asyncio.run(run())


def test_container_has_independent_expiry_no_mounts_and_only_loopback_port(monkeypatch):
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        return '127.0.0.1:43210' if args[:2] == ['docker','port'] else ''
    monkeypatch.setattr(canvas_login, 'command', command)
    browser = canvas_login.Browser(60)
    assert browser.start() == 'http://127.0.0.1:43210'
    args = calls[0]
    assert '--property=RuntimeMaxSec=60' in args
    assert '--property=ExecStopPost=/usr/bin/docker rm -f '+browser.name in args
    assert '--log-driver=none' in args
    assert args[args.index('--publish')+1] == '127.0.0.1::3000'
    assert '--volume' not in args and '-v' not in args and '--privileged' not in args
    assert '/config:rw,nosuid,nodev,size=512m' in args
    browser.close()
    assert calls[-1] == ['systemctl','--user','stop',browser.unit]


def test_serve_cleans_up_on_server_failure(tmp_path, monkeypatch):
    events=[]
    class FakeBrowser:
        def __init__(self, seconds): pass
        def start(self):
            events.append('start')
            raise CanvasError('browser_start_timeout')
        def close(self): events.append('close')
    monkeypatch.setattr(canvas_login, 'Browser', FakeBrowser)
    monkeypatch.setattr(canvas_login, 'tailnet_owner', lambda listen: 7)
    monkeypatch.setattr(canvas_login, 'tls_configuration', lambda config: ('127.0.0.1', None))
    args=SimpleNamespace(listen='100.1.2.3', operator_id=7, seconds=1, config=tmp_path, port=8769)
    with pytest.raises(CanvasError, match='browser_start_timeout'):
        asyncio.run(canvas_login.serve(args))
    assert events == ['start','close']


def test_whois_failure_denies_and_listen_must_be_owned(monkeypatch):
    def fail(*a, **k): raise CanvasError('browser_command_failed')
    monkeypatch.setattr(canvas_login,'command',fail)
    assert asyncio.run(canvas_login.identify('100.1.2.3')) == {}
    monkeypatch.setattr(canvas_login, 'command', lambda *a, **k: json.dumps({'Self':{'UserID':7,'TailscaleIPs':['100.1.2.3']}}))
    assert canvas_login.tailnet_owner('100.1.2.3') == 7
    with pytest.raises(CanvasError, match='listen_must_be_own_tailscale_address'):
        canvas_login.tailnet_owner('0.0.0.0')


def test_expiry_closes_active_websocket_and_stops_browser(tmp_path, monkeypatch):
    async def run():
        closed = asyncio.Event()
        async def socket(request):
            ws=web.WebSocketResponse()
            await ws.prepare(request)
            async for message in ws:
                await ws.send_str(message.data)
            closed.set()
            return ws
        backend_app=web.Application()
        backend_app.router.add_get('/socket',socket)
        async with TestServer(backend_app) as backend:
            class FakeBrowser:
                name='test-browser'
                def __init__(self,seconds): pass
                def start(self): return str(backend.make_url('')).rstrip('/')
                def close(self): events.append('closed')
            events=[]
            monkeypatch.setattr(canvas_login,'Browser',FakeBrowser)
            monkeypatch.setattr(canvas_login,'tailnet_owner',lambda listen:7)
            monkeypatch.setattr(canvas_login,'tls_configuration',lambda config:('127.0.0.1',None))
            async def identify(peer): return {'UserProfile':{'ID':7}}
            monkeypatch.setattr(canvas_login,'identify',identify)
            import socket as sockets
            with sockets.socket() as reserve:
                reserve.bind(('127.0.0.1',0))
                port=reserve.getsockname()[1]
            args=SimpleNamespace(listen='127.0.0.1', operator_id=7, port=port, seconds=.5,config=tmp_path)
            task=asyncio.create_task(canvas_login.serve(args))
            origin=f'http://127.0.0.1:{port}'
            async with ClientSession() as client:
                for _ in range(100):
                    try:
                        ws=await client.ws_connect(origin+'/socket',origin=origin)
                        break
                    except OSError:
                        await asyncio.sleep(.002)
                else:
                    pytest.fail('gateway did not start')
                await ws.send_str('hello')
                assert (await ws.receive()).data=='hello'
                message=await asyncio.wait_for(ws.receive(),2)
                assert message.type in (web.WSMsgType.CLOSE,web.WSMsgType.CLOSED)
                await ws.close()
            await asyncio.wait_for(task,2)
            await asyncio.wait_for(closed.wait(),1)
            assert events==['closed']
    asyncio.run(run())


def test_expired_collected_unit_is_already_clean(monkeypatch):
    def command(args):
        if args[0] == 'systemctl':
            raise CanvasError('browser_command_failed')
        return ''
    monkeypatch.setattr(canvas_login, 'command', command)
    canvas_login.Browser(1).close()


def test_cleanup_failure_is_reported_if_container_remains(monkeypatch):
    def command(args):
        if args[0] == 'systemctl':
            raise CanvasError('browser_command_failed')
        return 'container-id'
    monkeypatch.setattr(canvas_login, 'command', command)
    with pytest.raises(CanvasError, match='browser_cleanup_failed'):
        canvas_login.Browser(1).close()


def test_tls_private_key_must_be_private_and_owned(tmp_path, monkeypatch):
    monkeypatch.setattr(canvas_login, 'command', lambda *a: json.dumps({'Self':{'DNSName':'host.test.'}}))
    directory=tmp_path/'tls'
    directory.mkdir()
    key=directory/'server.key'
    key.write_text('test fixture')
    key.chmod(0o644)
    with pytest.raises(CanvasError, match='unsafe_tls_key'):
        canvas_login.tls_configuration(tmp_path)
