# SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
# SPDX-License-Identifier: Apache-2.0
import ipaddress,json,os,pathlib,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parent

def load_config():
 path=pathlib.Path(os.environ.get('MUSE_HOST_CONFIG',str(ROOT/'config.local.json')))
 if not path.exists():path=ROOT/'config.example.json'
 cfg=json.loads(path.read_text(encoding='utf-8-sig'))
 ipaddress.ip_address(cfg['bind'])
 for peer in cfg['allowed_peers']:ipaddress.ip_address(peer)
 if not cfg['allowed_peers']:raise ValueError('allowed_peers cannot be empty')
 for key in ('tts_port','relay_port'):
  if not isinstance(cfg[key],int) or not 1<=cfg[key]<=65535:raise ValueError('Invalid port')
 proxy=cfg.get('proxy','')
 if proxy:
  url=urllib.parse.urlparse(proxy)
  if url.scheme!='http' or not url.hostname or not url.port:raise ValueError('proxy must be an HTTP proxy URL')
  if cfg.get('relay_enabled') and (url.username or url.password):raise ValueError('Relay proxy authentication is not implemented')
 return cfg
