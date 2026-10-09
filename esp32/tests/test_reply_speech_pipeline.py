from pathlib import Path
import subprocess, tempfile, os, shlex
root=Path(__file__).absolute().parents[1]
source=(root/'components/muse/muse_chat_session.cpp').read_text(encoding='utf-8')
def fn(name):
 a=source.index('static void '+name+'(void)');b=source.index('{',a);depth=1;e=b+1
 while depth:
  depth+=(source[e]=='{')-(source[e]=='}');e+=1
 return source[a:e]
harness=r'''
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#include "muse_reply_phrase.h"
#define TEXT_MAX 32768
#define MIC_RATE 16000
#define TEXT_CHARS_PER_S 16
#define ESP_LOGI(...) ((void)0)
enum tts_t {TTS_NONE,TTS_QUEUED,TTS_ACTIVE,TTS_FINISHED};
struct msg_t {size_t len=0,spoken=0,phrase_end=0;char *audio_url=nullptr;bool done=false;tts_t tts=TTS_NONE;unsigned pcm_start=0,pcm_frames=0,phrase_start=0;};
struct prefetch_t {unsigned char *audio;size_t len=0,from=0,end=0;int message=0;unsigned ticket=0;bool started=false,ended=false,ok=false;};
struct {prefetch_t ahead;unsigned ticket=0,ticket_seq=0;unsigned char *mp3;msg_t msgs[2];int tts_msg=-1,nmsgs=1;char *texts;bool text=false,silent=false,mp3_ended=false,speech_failed=false;unsigned pcm_out=0,gen=1;size_t mp3_len=0;int kbps=0,down_rate=0,dec=0;} s_turn;
static std::vector<std::string> phrases;
static bool muse_settings_speaker_on(){return true;}
static bool muse_reply_tts_start(const char *text,unsigned,int,unsigned){phrases.emplace_back(text);return true;}
enum {M_TTS};static void mark(int){}
static void mp3dec_init(int *){}
static void show_reply_start(const msg_t &){}
static bool start_native_audio(msg_t &,int){return false;}
'''+fn('finish_phrase')+'\n'+fn('start_tts')+'\n'+fn('prefetch_tts')+r'''
int main(){
 char texts[TEXT_MAX*2]={0};unsigned char audio[524288],ahead[524288];s_turn.mp3=audio;s_turn.ahead.audio=ahead;s_turn.texts=texts;
 strcpy(texts,"第一句话。第二句话！最后一段");s_turn.msgs[0].done=true;
 for(int i=0;i<3;i++) {start_tts();assert(s_turn.tts_msg==0);s_turn.pcm_out+=16000;finish_phrase();
  assert(s_turn.msgs[0].tts==(i==2?TTS_FINISHED:TTS_QUEUED));}
 assert(phrases.size()==3);std::string joined;for(auto &p:phrases) joined+=p;assert(joined==texts);
 s_turn.msgs[0]=msg_t{};phrases.clear();strcpy(texts,"先回答你。");
 start_tts();assert(s_turn.tts_msg==0);finish_phrase();start_tts();assert(s_turn.tts_msg==-1);
 strcat(texts,"再说第二句。");start_tts();assert(s_turn.tts_msg==0);finish_phrase();
 strcat(texts,"这是结尾");start_tts();assert(s_turn.tts_msg==-1);
 s_turn.msgs[0].done=true;start_tts();assert(s_turn.tts_msg==0);finish_phrase();
 assert(s_turn.msgs[0].tts==TTS_FINISHED);joined.clear();for(auto &p:phrases)joined+=p;assert(joined==texts);
 // Empty lines and Markdown separators must not become speech jobs.
 s_turn.msgs[0]=msg_t{};phrases.clear();strcpy(texts,"你好。\n\n**第二句。**\n");s_turn.msgs[0].done=true;
 start_tts();prefetch_tts();assert(s_turn.ahead.started && phrases.size()==2);
 unsigned ticket=s_turn.ahead.ticket;s_turn.ahead.ended=true;s_turn.ahead.ok=true;s_turn.ahead.len=0;
 finish_phrase();start_tts();assert(s_turn.ticket==ticket && phrases.size()==2);finish_phrase();start_tts();
 assert(s_turn.msgs[0].tts==TTS_FINISHED);
 // A long reply must remain queued beyond the previous 4 KB limit.
 s_turn.msgs[0]=msg_t{};phrases.clear();texts[0]=0;
 for(int i=0;i<1000;i++)strcat(texts,"完整回答。");s_turn.msgs[0].done=true;
 while(s_turn.msgs[0].tts!=TTS_FINISHED){start_tts();if(s_turn.tts_msg>=0)finish_phrase();}
 joined.clear();for(auto &p:phrases)joined+=p;assert(joined==texts);
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'pipeline.cpp';p.write_text(harness,encoding='utf-8')
 exe=Path(tmp)/('pipeline.exe' if os.name=='nt' else 'pipeline')
 compiler=shlex.split(os.environ.get('CXX','c++'),posix=os.name!='nt')
 subprocess.run(compiler+['-std=c++17','-I',str(root/'components/muse'),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: complete replies, streamed tails, prefetch identity and long replies')
