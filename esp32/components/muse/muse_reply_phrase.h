/* SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
 * SPDX-License-Identifier: Apache-2.0
 */
#pragma once
#include <stddef.h>
#include <stdbool.h>
/* Return a complete UTF-8 phrase boundary; never split a code point. */
static inline size_t muse_reply_phrase_limit(const char *s, bool done, size_t limit, size_t comma) {
    size_t at=0, count=0;
    while (s[at]) {
        const unsigned char *p=(const unsigned char *)s+at;
        size_t n=p[0]<0x80?1:(p[0]>=0xc2 && p[0]<=0xdf?2:(p[0]>=0xe0 && p[0]<=0xef?3:(p[0]>=0xf0 && p[0]<=0xf4?4:0)));
        if (!n) return at;
        for (size_t k=1;k<n;k++) if (!p[k] || (p[k]&0xc0)!=0x80) return done?at:0;
        unsigned cp=p[0] & (n==1?0x7f:(n==2?0x1f:(n==3?0x0f:7)));
        for (size_t k=1;k<n;k++) cp=(cp<<6)|(p[k]&0x3f);
        at+=n;count++;
        if (cp==0x3002 || cp==0xff01 || cp==0xff1f || cp=='!' || cp=='?' || cp=='\n' ||
            (cp=='.' && (!s[at] || s[at]==' ' || s[at]=='\n')) ||
            (count>=comma && (cp==0xff0c || cp==0xff1b || cp==',' || cp==';')) || count>=limit)
            return at;
    }
    return done?at:0;
}

static inline size_t muse_reply_phrase(const char *s, bool done) {return muse_reply_phrase_limit(s,done,60,12);}
static inline size_t muse_reply_skip(const char *s) {
 size_t n=0;
 while (s[n]==' ' || s[n]=='\n' || s[n]=='\r' || s[n]=='\t' || s[n]=='*' || s[n]=='#' || s[n]=='`' || (s[n]=='-' && s[n+1]==' ')) n++;
 return n;
}
static inline bool muse_reply_has_words(const char *s, size_t len) {
 size_t at=0;
 while(at<len) {
  const unsigned char *p=(const unsigned char *)s+at;
  size_t n=p[0]<128?1:(p[0]<224?2:(p[0]<240?3:4));
  if(at+n>len) return false;
  unsigned cp=p[0]&(n==1?127:(n==2?31:(n==3?15:7)));
  for(size_t k=1;k<n;k++) cp=(cp<<6)|(p[k]&63);
  at+=n;
  if((cp>='a' && cp<='z') || (cp>='A' && cp<='Z') || (cp>='0' && cp<='9') ||
     (cp>=128 && !(cp>=0x2000 && cp<=0x206f) && !(cp>=0x3000 && cp<=0x303f) && !(cp>=0xff00 && cp<=0xff65))) return true;
 }
 return false;
}
