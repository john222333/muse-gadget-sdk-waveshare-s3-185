/* SPDX-License-Identifier: Apache-2.0 */
#include "gadget_user_config.h"
#include "sdkconfig.h"
#include "nvs.h"
#include "cJSON.h"
#include "lwip/inet.h"
#include "lwip/sockets.h"
#include <string.h>
#include <ctype.h>
#ifndef CONFIG_MUSE_REPLY_TTS_URL
#define CONFIG_MUSE_REPLY_TTS_URL ""
#endif
#ifndef CONFIG_MUSE_PC_RELAY_IP
#define CONFIG_MUSE_PC_RELAY_IP ""
#endif
static char token[256]=CONFIG_GADGET_SDK_TOKEN;
static char tts[256]=CONFIG_MUSE_REPLY_TTS_URL;
static char key[192];
static char relay[16]=CONFIG_MUSE_PC_RELAY_IP;
static bool phone_audio=true;
static const char *names[]={"sdk_token","tts_url","tts_key","relay_ip"};
static char *values[]={token,tts,key,relay};
static const size_t caps[]={sizeof(token),sizeof(tts),sizeof(key),sizeof(relay)};
esp_err_t gadget_user_config_init(void) {
 nvs_handle_t n;esp_err_t err=nvs_open("gadget_user",NVS_READWRITE,&n);
 if(err!=ESP_OK)return err;
 for(unsigned i=0;i<4;i++){size_t len=caps[i];nvs_get_str(n,names[i],values[i],&len);}
 uint8_t b;if(nvs_get_u8(n,"phone_audio",&b)==ESP_OK)phone_audio=b!=0;
 nvs_close(n);return ESP_OK;
}
const char *gadget_user_sdk_token(void){return token[0]?token:NULL;}
const char *gadget_user_tts_url(void){return tts;}
const char *gadget_user_tts_key(void){return key;}
const char *gadget_user_relay_ip(void){return relay;}
bool gadget_user_phone_audio(void){return phone_audio;}
static bool clean(const char *s){for(;*s;s++)if((unsigned char)*s<32 || *s==127)return false;return true;}
esp_err_t gadget_user_config_save(const char *json) {
 cJSON *obj=cJSON_Parse(json);if(!cJSON_IsObject(obj)){cJSON_Delete(obj);return ESP_ERR_INVALID_ARG;}
 bool any=false;esp_err_t err=ESP_OK;
 cJSON *item;
 cJSON_ArrayForEach(item,obj){
  bool known=item->string && !strcmp(item->string,"phone_audio");
  for(unsigned i=0;i<4;i++)if(item->string && !strcmp(item->string,names[i]))known=true;
  if(!known){err=ESP_ERR_INVALID_ARG;goto out;}
 }
 for(unsigned i=0;i<4;i++) {
  item=cJSON_GetObjectItemCaseSensitive(obj,names[i]);if(!item)continue;any=true;
  const char *s=cJSON_GetStringValue(item);
  if(!s || strlen(s)>=caps[i] || !clean(s)){err=ESP_ERR_INVALID_ARG;goto out;}
  if(i==0 && *s && (strncmp(s,"mgst_",5) || strlen(s)<12)){err=ESP_ERR_INVALID_ARG;goto out;}
  if(i==1 && *s) {
   if(strncmp(s,"http://",7) && strncmp(s,"https://",8)){err=ESP_ERR_INVALID_ARG;goto out;}
   const char *host=strstr(s,"://")+3;
   if(!*host || *host=='/' || *host=='?' || *host=='#'){err=ESP_ERR_INVALID_ARG;goto out;}
   for(const char *p=s;*p;p++)if(isspace((unsigned char)*p) || *p=='#'){err=ESP_ERR_INVALID_ARG;goto out;}
  }
  struct in_addr ip;if(i==3 && *s && inet_pton(AF_INET,s,&ip)!=1){err=ESP_ERR_INVALID_ARG;goto out;}
 }
 item=cJSON_GetObjectItemCaseSensitive(obj,"phone_audio");
 if(item){any=true;if(!cJSON_IsBool(item)){err=ESP_ERR_INVALID_ARG;goto out;}}
 if(!any){err=ESP_ERR_INVALID_ARG;goto out;}
 nvs_handle_t n;err=nvs_open("gadget_user",NVS_READWRITE,&n);if(err!=ESP_OK)goto out;
 for(unsigned i=0;i<4 && err==ESP_OK;i++){
  item=cJSON_GetObjectItemCaseSensitive(obj,names[i]);if(item)err=nvs_set_str(n,names[i],cJSON_GetStringValue(item));
 }
 item=cJSON_GetObjectItemCaseSensitive(obj,"phone_audio");
 if(err==ESP_OK && item)err=nvs_set_u8(n,"phone_audio",cJSON_IsTrue(item));
 if(err==ESP_OK)err=nvs_commit(n);
 nvs_close(n);
 out:cJSON_Delete(obj);return err;
}
