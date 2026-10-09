# SPDX-License-Identifier: Apache-2.0
import contextlib,hashlib,io,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(pathlib.Path(__file__).absolute().parents[1]))
import device
class DeviceSetupTests(unittest.TestCase):
 def test_manifest_checksum_and_path(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);data=b'public fixture';(root/'app.bin').write_bytes(data)
   manifest={'chip':'esp32s3','board':'waveshare-s3-185','files':[{'file':'app.bin','offset':'0x20000','sha256':hashlib.sha256(data).hexdigest()}]}
   (root/'manifest.json').write_text(json.dumps(manifest))
   self.assertEqual(device.manifest_files(root),['0x20000',str(root/'app.bin')])
   (root/'app.bin').write_bytes(b'changed')
   with self.assertRaises(ValueError):device.manifest_files(root)
   manifest['files'][0]['file']='../outside.bin';(root/'manifest.json').write_text(json.dumps(manifest))
   with self.assertRaises(ValueError):device.manifest_files(root)
 def test_config_acknowledgement_and_no_secret_echo(self):
  link=MagicMock();link.read.return_value=b'@user.config saved; reboot required\n'
  output=io.StringIO()
  with patch.object(device.serial,'Serial',return_value=link),patch.object(device.time,'sleep'),contextlib.redirect_stdout(output):
   device.send_config('TEST',{'sdk_token':'fixture-token','tts_key':'fixture-key'})
  sent=b''.join(call.args[0] for call in link.write.call_args_list)
  self.assertIn(b'>user.config=',sent);self.assertIn(b'>user.reboot\n',sent)
  self.assertNotIn('fixture-token',output.getvalue());self.assertNotIn('fixture-key',output.getvalue());link.close.assert_called_once()
 def test_invalid_config_does_not_reboot(self):
  link=MagicMock();link.read.return_value=b'@user.config invalid or storage error\n'
  with patch.object(device.serial,'Serial',return_value=link),patch.object(device.time,'sleep'):
   with self.assertRaises(ValueError):device.send_config('TEST',{'relay_ip':'invalid'})
  self.assertFalse(any(b'user.reboot' in call.args[0] for call in link.write.call_args_list));link.close.assert_called_once()
 def test_oversize_config_never_opens_port(self):
  with patch.object(device.serial,'Serial') as factory:
   with self.assertRaises(ValueError):device.send_config('TEST',{'tts_url':'x'*1100})
   factory.assert_not_called()
if __name__=='__main__':unittest.main()
