import importlib.util,http.client,threading,time,unittest,pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).absolute().parents[1]))
import voice_bridge as b
class FakeVoice:
 mode='normal';release=threading.Event();observed=threading.Event();attempts=0
 def __init__(self,*args,**kwargs):type(self).attempts+=1;self.number=type(self).attempts
 async def stream(self):
  if self.mode=='before':raise RuntimeError('test')
  self.observed.set()
  yield {'type':'audio','data':b'abcd'}
  if self.mode=='after' or (self.mode=='retry' and self.number==1):raise RuntimeError('test')
  if self.mode=='wait':
   while not self.release.is_set():await b.asyncio.sleep(.01)
  yield {'type':'audio','data':b'efgh'}
b.edge_tts.Communicate=FakeVoice
class StreamingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=b.http.server.ThreadingHTTPServer(('127.0.0.1',0),b.Handler)
  threading.Thread(target=cls.server.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
 def request(self,text=b'test'):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
  c.request('POST','/tts',body=text,headers={'Content-Type':'text/plain'})
  return c,c.getresponse()
 def test_complete_phrase_before_playback(self):
  import concurrent.futures
  FakeVoice.mode='wait';FakeVoice.release.clear();FakeVoice.observed.clear()
  with concurrent.futures.ThreadPoolExecutor() as pool:
   future=pool.submit(self.request)
   try:
    self.assertTrue(FakeVoice.observed.wait(2));time.sleep(.05);self.assertFalse(future.done())
   finally:FakeVoice.release.set()
   c,r=future.result(2);self.assertEqual(r.status,200);self.assertEqual(r.read(),b'abcdefgh');c.close()
 def test_retry_discards_incomplete_audio(self):
  FakeVoice.mode='retry';FakeVoice.attempts=0
  c,r=self.request();self.assertEqual(r.status,200);self.assertEqual(r.read(),b'abcdefgh');c.close()
  self.assertEqual(FakeVoice.attempts,2)
 def test_failure_before_audio(self):
  FakeVoice.mode='before';c,r=self.request();self.assertEqual(r.status,503);r.read();c.close()
 def test_failure_after_audio(self):
  FakeVoice.mode='after';c,r=self.request();self.assertEqual(r.status,503)
  self.assertNotIn(b'abcd',r.read());c.close()
 def test_metadata_only_skips_synthesis(self):
  FakeVoice.mode='normal';FakeVoice.attempts=0
  c,r=self.request(b'assistant-msg-541c09b3-7382-44cc-be05-4e7ba3c47712')
  self.assertEqual(r.status,204);self.assertEqual(r.read(),b'');c.close();self.assertEqual(FakeVoice.attempts,0)
 def test_validation(self):
  for text,status in [(b'',413),(b' '*10,400),(b'x'*1025,413),(b'\xff',400)]:
   c,r=self.request(text);self.assertEqual(r.status,status);r.read();c.close()
if __name__=='__main__':unittest.main()
