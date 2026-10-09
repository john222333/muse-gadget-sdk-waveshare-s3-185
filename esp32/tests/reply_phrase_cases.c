#include <assert.h>
#include <string.h>
#include "muse_reply_phrase.h"
int main(void) {
 assert(muse_reply_phrase("你好",false)==0);
 assert(muse_reply_phrase("你好",true)==6);
 assert(muse_reply_phrase("你好。第二句。",false)==9);
 assert(muse_reply_phrase("Hi! Next.",false)==3);
 assert(muse_reply_phrase("12.34",false)==0);
 assert(muse_reply_phrase("Hi. Next",false)==3);
 assert(muse_reply_phrase("\xe4\xbd",false)==0);
 assert(muse_reply_phrase("ok\xe4\xbd",true)==2);
 char text[401]={0};for(int i=0;i<100;i++) strcat(text,"甜");
 assert(muse_reply_phrase(text,false)==180);
 const char *s="你好呀，我现在可以用甜美的女声和你聊天啦。第二句话接着播放！最后一段";
 size_t total=0,len=strlen(s);int phrases=0;
 while(total<len) {size_t n=muse_reply_phrase(s+total,true);assert(n && n<=240);total+=n;phrases++;}
 assert(total==len && phrases==3);
 for(size_t available=1;available<=len;available++) {
  char partial[256];memcpy(partial,s,available);partial[available]=0;
  size_t n=muse_reply_phrase(partial,false);
  assert(n<=available);if(n) assert((unsigned char)s[n]<128 || ((unsigned char)s[n]&0xc0)!=0x80);
 }
 return 0;
}
