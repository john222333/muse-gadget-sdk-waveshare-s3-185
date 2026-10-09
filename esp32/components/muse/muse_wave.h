/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
typedef struct {size_t offset,bytes;unsigned rate,channels;} muse_wave_t;
static inline uint16_t muse_le16(const uint8_t *p){return p[0]|((uint16_t)p[1]<<8);}
static inline uint32_t muse_le32(const uint8_t *p){return p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static inline bool muse_wave_parse(const uint8_t *data,size_t length,muse_wave_t *out) {
 if(length<12 || memcmp(data,"RIFF",4) || memcmp(data+8,"WAVE",4))return false;
 size_t end=(size_t)muse_le32(data+4)+8;if(end>length || end<12)return false;
 bool format=false,pcm=false,body=false;muse_wave_t wave={0,0,0,0};
 for(size_t off=12;off<=end && end-off>=8;) {
  size_t n=muse_le32(data+off+4);off+=8;if(n>end-off)return false;
  if(!memcmp(data+off-8,"fmt ",4)) {
   if(n<16)return false;
   wave.channels=muse_le16(data+off+2);wave.rate=muse_le32(data+off+4);
   pcm=muse_le16(data+off)==1 && muse_le16(data+off+14)==16;
   if((wave.channels!=1 && wave.channels!=2) || wave.rate<8000 || wave.rate>96000)return false;
   if(muse_le16(data+off+12)!=wave.channels*2 || muse_le32(data+off+8)!=wave.rate*wave.channels*2)return false;
   format=true;
  } else if(!memcmp(data+off-8,"data",4)){wave.offset=off;wave.bytes=n;body=true;}
  if(n+(n&1)>end-off)return false;
  off+=n+(n&1);
 }
 if(!format || !pcm || !body || !wave.bytes || wave.bytes%(wave.channels*2))return false;
 *out=wave;return true;
}
