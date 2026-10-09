# SPDX-License-Identifier: Apache-2.0
import os, pathlib, shlex, subprocess, tempfile, unittest
ROOT=pathlib.Path(__file__).absolute().parents[1]
class UserConfigTests(unittest.TestCase):
 def test_validation_and_persistent_overrides(self):
  src=pathlib.Path(os.environ.get('CJSON_DIR',ROOT/'managed_components/espressif__cjson/cJSON'))
  if not (src/'cJSON.c').exists():self.skipTest('Build first or provide CJSON_DIR')
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'lwip').mkdir()
   (p/'esp_err.h').write_text('#pragma once\ntypedef int esp_err_t;\n#define ESP_OK 0\n#define ESP_ERR_INVALID_ARG 1\n')
   (p/'sdkconfig.h').write_text('#define CONFIG_GADGET_SDK_TOKEN ""\n')
   (p/'lwip/inet.h').write_text('#include <winsock2.h>\n#include <ws2tcpip.h>\n' if os.name=='nt' else '#include <arpa/inet.h>\n')
   (p/'lwip/sockets.h').write_text('')
   (p/'nvs.h').write_text('#pragma once\n#include <stddef.h>\n#include <stdint.h>\ntypedef int nvs_handle_t;\n#define NVS_READWRITE 1\nint nvs_open(const char*,int,int*);int nvs_get_str(int,const char*,char*,size_t*);int nvs_get_u8(int,const char*,uint8_t*);int nvs_set_str(int,const char*,const char*);int nvs_set_u8(int,const char*,uint8_t);int nvs_commit(int);void nvs_close(int);\n')
   (p/'test.c').write_text(r'''
#include <assert.h>
#include <string.h>
#include "gadget_user_config.h"
#include "nvs.h"
static char saved[4][256];static int commits;static uint8_t phone=1;
static const char *keys[]={"sdk_token","tts_url","tts_key","relay_ip"};
int nvs_open(const char*a,int b,int*c){*c=1;return 0;}
int nvs_get_str(int n,const char*k,char*out,size_t*len){for(int i=0;i<4;i++)if(!strcmp(k,keys[i])){if(strlen(saved[i])+1>*len)return 1;strcpy(out,saved[i]);return 0;}return 1;}
int nvs_get_u8(int n,const char*k,uint8_t*v){*v=phone;return 0;}
int nvs_set_str(int n,const char*k,const char*v){for(int i=0;i<4;i++)if(!strcmp(k,keys[i]))strcpy(saved[i],v);return 0;}
int nvs_set_u8(int n,const char*k,uint8_t v){phone=v;return 0;}
int nvs_commit(int n){commits++;return 0;}void nvs_close(int n){}
int main(){
 assert(gadget_user_config_init()==0);assert(!gadget_user_sdk_token());
 assert(gadget_user_config_save("{\"sdk_token\":\"mgst_" "unit_test_fixture\",\"relay_ip\":\"192.0.2.10\",\"tts_url\":\"https://example.com/tts\",\"tts_key\":\"fixture-key\",\"phone_audio\":false}")==0);
 assert(commits==1);assert(gadget_user_config_init()==0);
 assert(!strcmp(gadget_user_relay_ip(),"192.0.2.10"));assert(!strcmp(gadget_user_tts_url(),"https://example.com/tts"));assert(!gadget_user_phone_audio());assert(gadget_user_sdk_token());
 const char *bad[]={"{}","[]","{\"sdk_token\":1}","{\"sdk_token\":\"wrong\"}","{\"relay_ip\":\"999.1.2.3\"}","{\"tts_url\":\"file:///etc/passwd\"}","{\"tts_key\":\"a\\r\\nInjected: true\"}","{\"unknown\":1}","{\"phone_audio\":\"true\"}"};
 for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++)assert(gadget_user_config_save(bad[i])!=0);
 assert(commits==1);assert(gadget_user_config_save("{\"sdk_token\":\"\",\"relay_ip\":\"\",\"tts_url\":\"\",\"tts_key\":\"\",\"phone_audio\":true}")==0);
 assert(gadget_user_config_init()==0);assert(!gadget_user_sdk_token());assert(!*gadget_user_tts_url());assert(!*gadget_user_relay_ip());assert(gadget_user_phone_audio());
}
''')
   exe=p/('check.exe' if os.name=='nt' else 'check')
   command=shlex.split(os.environ.get('CC','cc'),posix=os.name!='nt')+['-I',str(p),'-I',str(src),'-I',str(ROOT/'components/gadget_user_config'),str(p/'test.c'),str(ROOT/'components/gadget_user_config/gadget_user_config.c'),str(src/'cJSON.c'),'-o',str(exe)]
   if os.name=='nt':command+=['-lws2_32']
   subprocess.run(command,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':unittest.main()
