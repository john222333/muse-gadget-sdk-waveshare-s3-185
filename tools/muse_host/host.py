# SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
# SPDX-License-Identifier: Apache-2.0
import argparse,asyncio,os,pathlib,threading

def main():
 parser=argparse.ArgumentParser(description='Muse speech and optional TLS relay')
 parser.add_argument('--config',type=pathlib.Path)
 parser.add_argument('--mode',choices=['voice','relay','all'],default='all')
 args=parser.parse_args()
 if args.config:os.environ['MUSE_HOST_CONFIG']=str(args.config.resolve())
 from host_config import load_config
 cfg=load_config()
 if args.mode=='relay':
  import muse_pc_relay
  asyncio.run(muse_pc_relay.main());return
 if not cfg.get('online_speech_consent'):raise SystemExit('Online speech consent is required; see config.example.json and README.')
 if args.mode=='all' and cfg.get('relay_enabled'):
  if not cfg.get('proxy'):raise SystemExit('The relay requires an HTTP proxy.')
  import muse_pc_relay
  threading.Thread(target=lambda:asyncio.run(muse_pc_relay.main()),daemon=True).start()
 import voice_bridge
 voice_bridge.main()
if __name__=='__main__':main()
