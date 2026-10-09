# SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
# SPDX-License-Identifier: Apache-2.0
import asyncio,http.server,json,logging,pathlib,sys,threading,time,re
from host_config import load_config
from tts_transport import install_short_close
import edge_tts
install_short_close()
_cfg=load_config()
BIND=_cfg['bind']
PEERS=set(_cfg['allowed_peers'])
LIMIT=512*1024
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
slot=threading.BoundedSemaphore(2)
def settings():
 cfg=load_config()
 return dict(cfg['speech'],proxy=cfg.get('proxy') or None)
def speech_text(text):
 # Keep useful language and ordinary numbers; exclude machine identifiers and markup.
 text=re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)',r'\1',text)
 text=re.sub(r'https?://[^\s<>]+','',text)
 text=re.sub(r'\ue200.*?\ue201','',text)
 text=re.sub(r'(?i)(?:assistant[-_]?(?:msg|message)[-_: ]*)?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}','',text)
 text=re.sub(r'(?i)(?:turn\d+(?:search|view|fetch)\d+|(?:message|request|trace|session|conversation)[ _-]*id\s*[:=：]?\s*[a-z0-9_.-]{12,})','',text)
 def opaque(match):
  token=match.group()
  return '' if sum(c.isdigit() for c in token)>=2 and ('-' in token or '_' in token or len(token)>=24) else token
 text=re.sub(r'[A-Za-z0-9_-]{16,}',opaque,text)
 text=re.sub(r'(?i)(?:消息|请求|会话|任务|追踪)(?:编号|标识|ID)\s*[:：=]?\s*(?=[，。；\s]*$)','',text)
 text=re.sub(r'(?i)\b(?:UUID|message_id|assistant_msg|trace_id)\b\s*[:=：]?\s*(?=[，。；\s]*$)','',text)
 text=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]','',text)
 text=re.sub(r'[`*#]+','',text)
 return ' '.join(text.split()).strip(' ,.;:，。；：')

async def synthesize(text,cfg,send):
 # Complete one short phrase before publishing: retries cannot cut or repeat speech.
 for attempt in range(2):
  async def collect():
   data=bytearray()
   voice=edge_tts.Communicate(text,cfg['voice'],rate=cfg['rate'],pitch=cfg['pitch'],proxy=cfg['proxy'],connect_timeout=3,receive_timeout=3)
   async for part in voice.stream():
    if part['type']=='audio':
     data.extend(part['data'])
     if len(data)>LIMIT:raise ValueError('Audio too large')
   if not data:raise ValueError('No audio returned')
   return bytes(data)
  try:
   audio=await asyncio.wait_for(collect(),timeout=5)
   break
  except Exception:
   if attempt:raise
   logging.info('Retrying incomplete speech phrase')
 send(audio)
 return len(audio)
class Handler(http.server.BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*args):pass
 def reply(self,status,data,kind='text/plain; charset=utf-8'):
  self.send_response(status);self.send_header('Content-Type',kind)
  self.send_header('Content-Length',str(len(data)));self.send_header('Connection','close');self.end_headers()
  self.close_connection=True
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
 def do_GET(self):
  if self.client_address[0] not in PEERS:return self.reply(403,b'Forbidden')
  if self.path!='/health':return self.reply(404,b'Not found')
  self.reply(200,json.dumps({'ready':True,'voice':settings()['voice']}).encode(),'application/json')
 def do_POST(self):
  if self.client_address[0] not in PEERS:return self.reply(403,b'Forbidden')
  if self.path!='/tts':return self.reply(404,b'Not found')
  try:length=int(self.headers.get('Content-Length','0'))
  except ValueError:return self.reply(400,b'Invalid length')
  if not 0<length<=1024:return self.reply(413,b'Text too long')
  self.connection.settimeout(5)
  try:
   raw=self.rfile.read(length)
   if len(raw)!=length:return self.reply(400,b'Incomplete text')
   text=raw.decode('utf-8').strip()
  except (OSError,UnicodeError):return self.reply(400,b'Invalid text')
  if not text:return self.reply(400,b'Empty text')
  text=speech_text(text)
  if not text:return self.reply(204,b'')
  if not slot.acquire(blocking=False):return self.reply(503,b'Speech busy')
  started=False;begin=time.monotonic()
  def send(data):
   nonlocal started
   if not started:
    self.send_response(200);self.send_header('Content-Type','audio/mpeg')
    self.send_header('Transfer-Encoding','chunked');self.send_header('Connection','close');self.end_headers()
    started=True;logging.info('Speech first audio: %.2fs',time.monotonic()-begin)
   self.wfile.write(('%X\r\n'%len(data)).encode()+data+b'\r\n');self.wfile.flush()
  try:
   total=asyncio.run(asyncio.wait_for(synthesize(text,settings(),send),timeout=12))
   self.wfile.write(b'0\r\n\r\n');self.wfile.flush()
   logging.info('Speech delivered: %d bytes in %.2fs',total,time.monotonic()-begin)
  except Exception as error:
   logging.info('Speech unavailable: %s',type(error).__name__)
   if not started:self.reply(503,b'Speech temporarily unavailable')
   # A partial stream is deliberately not terminated as a successful download.
  finally:self.close_connection=True;slot.release()
def main():
 cfg=load_config()
 if not cfg.get('online_speech_consent'):raise SystemExit('Set online_speech_consent=true after reviewing the privacy notice.')
 server=http.server.ThreadingHTTPServer((cfg['bind'],cfg['tts_port']),Handler);server.daemon_threads=True
 logging.info('Muse reply speech ready on %s:%d',cfg['bind'],cfg['tts_port'])
 try:server.serve_forever()
 finally:server.server_close()
if __name__=='__main__':main()
