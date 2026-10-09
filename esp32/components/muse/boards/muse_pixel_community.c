/* SPDX-License-Identifier: Apache-2.0 */
/* Original geometric community avatar; no upstream character artwork. */
#include "muse_pixel.h"
#include <math.h>
#include <string.h>
#include "esp_attr.h"
static EXT_RAM_BSS_ATTR uint8_t frame[MUSE_PX_W*MUSE_PX_H];
static uint16_t palette[4];static int size=360;
static uint16_t rgb(uint32_t c){return ((c>>19)&31)<<11 | ((c>>10)&63)<<5 | ((c>>3)&31);}
uint32_t muse_pixel_accent(muse_mode_t mode){
 switch(mode){case MUSE_MODE_LISTENING:return 0x5edc9c;case MUSE_MODE_THINKING:return 0xf4c86a;case MUSE_MODE_SPEAKING:return 0x73baff;case MUSE_MODE_ERROR:return 0xff778a;case MUSE_MODE_OFF:return 0x64748b;default:return 0x73baff;}
}
static void rect(int x,int y,int w,int h,uint8_t color){
 for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)if(xx>=0 && xx<64 && yy>=0 && yy<64)frame[yy*64+xx]=color;
}
void muse_pixel_set_size(int px){size=px>0?px:1;}
void muse_pixel_render(const muse_pose_t *pose){
 memset(frame,0,sizeof(frame));palette[0]=rgb(0x0b1320);palette[1]=rgb(muse_pixel_accent(pose->mode));palette[2]=rgb(0xe7f3ff);palette[3]=rgb(0x142335);
 int bob=(int)(sinf(pose->t*2.0f)*1.5f);
 rect(17,17+bob,30,29,1);rect(14,21+bob,36,21,1);
 rect(19,22+bob,26,19,3);rect(30,11+bob,4,7,1);rect(28,9+bob,8,4,2);
 bool blink=fmodf(pose->t,5.0f)<0.16f || pose->mode==MUSE_MODE_OFF;
 rect(23,27+bob,5,blink?1:5,2);rect(36,27+bob,5,blink?1:5,2);
 int mouth=pose->mode==MUSE_MODE_SPEAKING?2+(int)(pose->level*6):2;
 if(mouth>8)mouth=8;
 rect(28,35+bob,8,mouth,2);rect(25,47+bob,14,3,1);rect(20,50+bob,24,4,1);
}
void muse_pixel_scale(uint16_t *dst,int stride,int x0,int x1,int y0,int y1){
 for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){
  int sx=x*64/size,sy=y*64/size;
  dst[(y-y0)*stride+x-x0]=sx>=0 && sx<64 && sy>=0 && sy<64?palette[frame[sy*64+sx]]:palette[0];
 }
}
