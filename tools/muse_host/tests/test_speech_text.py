import importlib.util,pathlib,unittest
import sys
sys.path.insert(0,str(pathlib.Path(__file__).absolute().parents[1]))
import voice_bridge as b
class TextTests(unittest.TestCase):
 def test_ids(self):
  self.assertEqual(b.speech_text('介绍完了。 assistant-msg-541c09b3-7382-44cc-be05-4e7ba3c47712'),'介绍完了')
  self.assertEqual(b.speech_text('消息编号：541c09b3-7382-44cc-be05-4e7ba3c47712'),'')
  self.assertEqual(b.speech_text('eab45a023ca34bd79cdfaac135643566'),'')
 def test_useful_numbers_and_english(self):
  text='ESP32 支持 WiFi，温度 25.5 度，时间 2026-10-08，电压 3.3V'
  self.assertEqual(b.speech_text(text),text)
  self.assertEqual(b.speech_text('electromagnetism and troubleshooting'),'electromagnetism and troubleshooting')
 def test_markup_and_citations(self):
  self.assertEqual(b.speech_text('**完成了** [说明](https://example.com) \ue200cite\ue202turn0search0\ue201'),'完成了 说明')
 def test_only_markup(self):
  self.assertEqual(b.speech_text(' \n **#``` 。'),'')
if __name__=='__main__':unittest.main()
