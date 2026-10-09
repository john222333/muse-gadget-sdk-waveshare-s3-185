# SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
# SPDX-License-Identifier: Apache-2.0
import aiohttp

def install_short_close():
 """Bound only the websocket close handshake; keep audio reception unchanged."""
 original=aiohttp.ClientSession.ws_connect
 if getattr(original,'_muse_short_close',False):return
 def connect(session,*args,**kwargs):
  kwargs.setdefault('timeout',aiohttp.ClientWSTimeout(ws_close=0.1))
  return original(session,*args,**kwargs)
 connect._muse_short_close=True
 aiohttp.ClientSession.ws_connect=connect
