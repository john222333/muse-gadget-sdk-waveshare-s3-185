# SPDX-License-Identifier: Apache-2.0
import os,pathlib,shlex,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).absolute().parents[1]
class AudioReplyTests(unittest.TestCase):
 def test_reference_and_wave_boundaries(self):
  src=pathlib.Path(os.environ.get('CJSON_DIR',ROOT/'managed_components/espressif__cjson/cJSON'))
  if not (src/'cJSON.c').exists():self.skipTest('Build first or provide CJSON_DIR')
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);source=p/'audio.c'
   source.write_text(r'''
#include <assert.h>
#include <string.h>
#include "muse_audio_reply.h"
#include "muse_wave.h"
static unsigned char wave_data[]={82,73,70,70,52,0,0,0,87,65,86,69,102,109,116,32,16,0,0,0,1,0,2,0,128,62,0,0,0,250,0,0,4,0,16,0,100,97,116,97,16,0,0,0,1,0,255,255,1,0,255,255,1,0,255,255,1,0,255,255};
int main(){
 cJSON *j=cJSON_Parse("{\"items\":[{\"type\":\"file\",\"mime_type\":\"audio/mpeg\",\"url\":\"https://example.com/a.mp3?signature=fixture\"}]}");
 assert(!strcmp(muse_audio_reference(j,false,0),"https://example.com/a.mp3?signature=fixture"));cJSON_Delete(j);
 j=cJSON_Parse("{\"audio\":{\"download_url\":\"/media/sample.wav\"}}");assert(!strcmp(muse_audio_reference(j,false,0),"/media/sample.wav"));cJSON_Delete(j);
 j=cJSON_Parse("{\"items\":[{\"mime_type\":\"image/png\",\"url\":\"https://example.com/image.png\"}]}");assert(!muse_audio_reference(j,false,0));cJSON_Delete(j);
 assert(muse_audio_url_valid("/media/fixture.mp3"));assert(muse_audio_url_valid("https://example.com/audio"));
 assert(!muse_audio_url_valid("file:///etc/passwd"));assert(!muse_audio_url_valid("//example.com/audio"));assert(!muse_audio_url_valid("https://example.com/\r\nheader"));
 muse_wave_t info;assert(muse_wave_parse(wave_data,sizeof(wave_data),&info));assert(info.channels==2 && info.rate==16000 && info.bytes==16 && info.offset==44);
 for(unsigned n=0;n<sizeof(wave_data);n++)assert(!muse_wave_parse(wave_data,n,&info));
 unsigned char bad[sizeof(wave_data)];memcpy(bad,wave_data,sizeof(bad));bad[20]=3;assert(!muse_wave_parse(bad,sizeof(bad),&info));
 memcpy(bad,wave_data,sizeof(bad));bad[34]=24;assert(!muse_wave_parse(bad,sizeof(bad),&info));
 memcpy(bad,wave_data,sizeof(bad));memset(bad+40,255,4);assert(!muse_wave_parse(bad,sizeof(bad),&info));
}
''')
   exe=p/('audio.exe' if os.name=='nt' else 'audio')
   cmd=shlex.split(os.environ.get('CC','cc'),posix=os.name!='nt')+['-I',str(src),'-I',str(ROOT/'components/muse'),str(source),str(src/'cJSON.c'),'-o',str(exe)]
   subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':unittest.main()
