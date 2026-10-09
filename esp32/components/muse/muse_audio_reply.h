/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include "cJSON.h"
#include <stdbool.h>
#include <string.h>
/* Recognise audio references, never speak their URLs as text. */
static inline const char *muse_audio_reference(const cJSON *node, bool audio, unsigned depth) {
 if(!node || depth>5)return NULL;
 if(cJSON_IsObject(node)) {
  const char *mime=cJSON_GetStringValue(cJSON_GetObjectItemCaseSensitive(node,"mime_type"));
  if(!mime)mime=cJSON_GetStringValue(cJSON_GetObjectItemCaseSensitive(node,"content_type"));
  const char *type=cJSON_GetStringValue(cJSON_GetObjectItemCaseSensitive(node,"type"));
  audio=audio || (mime && !strncmp(mime,"audio/",6)) || (type && !strcmp(type,"audio"));
  const char *direct=cJSON_GetStringValue(cJSON_GetObjectItemCaseSensitive(node,"audio_url"));
  if(direct && *direct)return direct;
  if(audio) {
   const char *keys[]={"url","download_url","uri","src"};
   for(unsigned i=0;i<4;i++){const char *s=cJSON_GetStringValue(cJSON_GetObjectItemCaseSensitive(node,keys[i]));if(s && *s)return s;}
  }
  const char *containers[]={"audio","items","attachments","content","files","file","message"};
  for(unsigned i=0;i<7;i++) {
   const char *s=muse_audio_reference(cJSON_GetObjectItemCaseSensitive(node,containers[i]),audio || i==0,depth+1);
   if(s)return s;
  }
 } else if(cJSON_IsArray(node)) {
  const cJSON *child;cJSON_ArrayForEach(child,node){const char *s=muse_audio_reference(child,audio,depth+1);if(s)return s;}
 }
 return NULL;
}
static inline bool muse_audio_url_valid(const char *url) {
 if(!url || strlen(url)>2047)return false;
 if(strncmp(url,"https://",8) && strncmp(url,"http://",7) && url[0]!='/')return false;
 if(url[0]=='/' && url[1]=='/')return false;
 for(const unsigned char *p=(const unsigned char*)url;*p;p++)if(*p<33 || *p==127)return false;
 return true;
}
