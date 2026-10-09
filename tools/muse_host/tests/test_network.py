# SPDX-License-Identifier: Apache-2.0
import asyncio, pathlib, ssl, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).absolute().parents[1]))
import muse_pc_relay as relay

def client_hello(host):
    incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
    client = ssl.create_default_context().wrap_bio(incoming, outgoing, server_hostname=host)
    try:
        client.do_handshake()
    except ssl.SSLWantReadError:
        pass
    return outgoing.read()

class RelayNetworkTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.old_peers, self.old_proxy = relay.ALLOWED_PEERS, relay.PROXY
        relay.ALLOWED_PEERS = {'127.0.0.1'}
        self.received = []
        async def proxy(reader, writer):
            try:
                request = await reader.readuntil(b'\r\n\r\n')
                self.received.append(request)
                writer.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
                await writer.drain()
                data = await reader.readexactly(len(self.hello) + len(b'device-payload'))
                self.received.append(data)
                writer.write(b'upstream-reply')
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
        self.proxy = await asyncio.start_server(proxy, '127.0.0.1', 0)
        relay.PROXY = ('127.0.0.1', self.proxy.sockets[0].getsockname()[1])
        self.server = await asyncio.start_server(relay.handle, '127.0.0.1', 0)

    async def asyncTearDown(self):
        self.server.close(); self.proxy.close()
        await self.server.wait_closed(); await self.proxy.wait_closed()
        relay.ALLOWED_PEERS, relay.PROXY = self.old_peers, self.old_proxy

    async def connect(self, host):
        self.hello = client_hello(host)
        reader, writer = await asyncio.open_connection('127.0.0.1', self.server.sockets[0].getsockname()[1])
        writer.write(self.hello + b'device-payload'); await writer.drain()
        try:
            try:
                return await asyncio.wait_for(reader.read(), 2)
            except ConnectionResetError:
                return b''
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionResetError:
                pass

    async def test_connect_and_bidirectional_bytes(self):
        self.assertEqual(await self.connect('hatch.metaaivm.com'), b'upstream-reply')
        self.assertEqual(self.received[0], b'CONNECT hatch.metaaivm.com:443 HTTP/1.1\r\nHost: hatch.metaaivm.com:443\r\n\r\n')
        self.assertEqual(self.received[1], self.hello + b'device-payload')

    async def test_non_muse_host_never_reaches_proxy(self):
        self.assertEqual(await self.connect('example.com'), b'')
        self.assertEqual(self.received, [])

    async def test_unlisted_peer_never_reaches_proxy(self):
        relay.ALLOWED_PEERS = set()
        self.assertEqual(await self.connect('api.muse.ai'), b'')
        self.assertEqual(self.received, [])

    def test_domain_boundaries_and_real_client_hello(self):
        for name in ('muse.ai', 'api.muse.ai', 'hatch.metaaivm.com'):
            self.assertTrue(relay.allowed_host(name))
            self.assertEqual(relay.parse_sni(client_hello(name)[5:]), name)
        for name in ('evil-muse.ai', 'muse.ai.example.com', 'example.com'):
            self.assertFalse(relay.allowed_host(name))

if __name__ == '__main__':
    unittest.main()
