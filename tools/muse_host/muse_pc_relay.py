# SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
# SPDX-License-Identifier: Apache-2.0
import asyncio,logging,struct,sys
from urllib.parse import urlparse
from host_config import load_config
cfg=load_config()
BIND=cfg['bind']
_proxy=urlparse(cfg.get('proxy') or 'http://127.0.0.1:7890')
PROXY=(_proxy.hostname,_proxy.port)
ALLOWED_PEERS=set(cfg['allowed_peers'])
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
def allowed_host(host):
 return any(host==s or host.endswith('.'+s) for s in ('muse.ai','metaaivm.com'))
def parse_sni(data):
 if data[0]!=1:raise ValueError('Expected TLS ClientHello')
 p=4+2+32;p+=1+data[p]
 n=int.from_bytes(data[p:p+2],'big');p+=2+n
 p+=1+data[p]
 n=int.from_bytes(data[p:p+2],'big');p+=2;end=p+n
 while p+4<=end:
  typ,size=struct.unpack('!HH',data[p:p+4]);p+=4;ext=data[p:p+size];p+=size
  if typ==0:
   q=2
   while q+3<=len(ext):
    kind=ext[q];length=int.from_bytes(ext[q+1:q+3],'big');q+=3
    if kind==0:return ext[q:q+length].decode('ascii').lower()
    q+=length
 raise ValueError('Missing server name')
async def pipe(src,dst):
 while True:
  data=await src.read(65536)
  if not data:return
  dst.write(data);await dst.drain()
async def handle(reader,writer):
 upstream=None;peer=writer.get_extra_info('peername')[0];host='unknown'
 try:
  if peer not in ALLOWED_PEERS:raise ValueError('Peer not allowed')
  records=b'';handshake=b''
  while len(handshake)<4 or len(handshake)<4+int.from_bytes(handshake[1:4],'big'):
   header=await asyncio.wait_for(reader.readexactly(5),10)
   if header[0]!=22:raise ValueError('Expected TLS handshake')
   size=int.from_bytes(header[3:5],'big')
   if size>18432 or len(records)>65536:raise ValueError('Oversized handshake')
   body=await reader.readexactly(size);records+=header+body;handshake+=body
  host=parse_sni(handshake)
  if not allowed_host(host):raise ValueError('Host not allowed')
  rx,upstream=await asyncio.wait_for(asyncio.open_connection(*PROXY),10)
  upstream.write(('CONNECT '+host+':443 HTTP/1.1\r\nHost: '+host+':443\r\n\r\n').encode());await upstream.drain()
  response=await asyncio.wait_for(rx.readuntil(b'\r\n\r\n'),20)
  if response.split(b'\r\n')[0].split()[1]!=b'200':raise ValueError('Proxy CONNECT refused')
  upstream.write(records);await upstream.drain();logging.info('Connected %s -> %s',peer,host)
  tasks=[asyncio.create_task(pipe(reader,upstream)),asyncio.create_task(pipe(rx,writer))]
  done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
  for t in pending:t.cancel()
  await asyncio.gather(*tasks,return_exceptions=True)
 except Exception as error:logging.info('Connection %s to %s: %s',peer,host,type(error).__name__)
 finally:
  writer.close()
  if upstream:upstream.close()
async def main():
 if not cfg.get('relay_enabled') or not cfg.get('proxy'):raise SystemExit('Enable relay_enabled and configure an HTTP proxy first.')
 server=await asyncio.start_server(handle,BIND,cfg['relay_port'])
 logging.info('Muse encrypted relay listening on %s:%d',BIND,cfg['relay_port'])
 async with server:await server.serve_forever()
if __name__=='__main__':asyncio.run(main())
