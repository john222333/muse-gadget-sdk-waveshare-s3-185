/* SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
 * SPDX-License-Identifier: Apache-2.0
 */
#include "muse_reply_tts.h"
#include "gadget_user_config.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <stdatomic.h>
#include "sdkconfig.h"
#include "esp_http_client.h"
#include "esp_crt_bundle.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/idf_additions.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#ifndef CONFIG_MUSE_REPLY_TTS_URL
#define CONFIG_MUSE_REPLY_TTS_URL ""
#endif
#define AUDIO_LIMIT (512 * 1024)
#define CHUNK 4096
typedef struct {
    muse_reply_tts_result_t result;
    unsigned epoch;
    bool mpeg;
    char text[1024];
    bool native;
    char url[2048];
} job_t;
static QueueHandle_t results;
static atomic_uint epoch;
static atomic_uint workers;
static bool publish(job_t *job, muse_reply_tts_result_t *part) {
    while (job->epoch==atomic_load(&epoch)) {
        if (xQueueSend(results,part,pdMS_TO_TICKS(50))==pdTRUE) return true;
    }
    free(part->audio);
    return false;
}
static esp_err_t receive(esp_http_client_event_t *event) {
    job_t *job=event->user_data;
    if (event->event_id==HTTP_EVENT_ON_HEADER && event->header_key && event->header_value &&
        !strcasecmp(event->header_key,"Content-Type"))
        job->mpeg=!strncasecmp(event->header_value,"audio/mpeg",10) || !strncasecmp(event->header_value,"audio/mp3",9) || (job->native && (!strncasecmp(event->header_value,"application/octet-stream",24) || !strncasecmp(event->header_value,"audio/wav",9) || !strncasecmp(event->header_value,"audio/x-wav",11)));
    return ESP_OK;
}
static void run(void *arg) {
    job_t *job=arg;
    esp_http_client_config_t config={
        .url=job->native?job->url:gadget_user_tts_url(),.timeout_ms=15000,
        .method=job->native?HTTP_METHOD_GET:HTTP_METHOD_POST,.event_handler=receive,.user_data=job,
        .crt_bundle_attach=esp_crt_bundle_attach,.disable_auto_redirect=true,
        .buffer_size=2048,.buffer_size_tx=1024,
    };
    esp_http_client_handle_t client=esp_http_client_init(&config);
    size_t total=0;
    bool ok=false;
    if (client && job->epoch==atomic_load(&epoch)) {
        if(!job->native)esp_http_client_set_header(client,"Content-Type","text/plain; charset=utf-8");
        if(!job->native && gadget_user_tts_key()[0]) {
            char auth[208];snprintf(auth,sizeof(auth),"Bearer %s",gadget_user_tts_key());
            esp_http_client_set_header(client,"Authorization",auth);
        }
        size_t len=job->native?0:strlen(job->text);
        if (esp_http_client_open(client,len)==ESP_OK &&
            (!len || esp_http_client_write(client,job->text,len)==(int)len) &&
            esp_http_client_fetch_headers(client)>=0) {
            if (esp_http_client_get_status_code(client)==204 && !job->native) ok=true;
            else if (esp_http_client_get_status_code(client)==200 && job->mpeg) {
            while (job->epoch==atomic_load(&epoch)) {
                muse_reply_tts_result_t part=job->result;
                part.audio=heap_caps_malloc(CHUNK,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
                if (!part.audio) break;
                int n=esp_http_client_read(client,(char *)part.audio,CHUNK);
                if (n<=0) {
                    free(part.audio);
                    ok=n==0 && total>0 && esp_http_client_is_complete_data_received(client);
                    break;
                }
                total+=n;
                if (total>AUDIO_LIMIT) {free(part.audio);break;}
                part.size=n;part.ok=true;
                if (!publish(job,&part)) break;
            }
            }
        }
    }
    job->result.unavailable=!client || esp_http_client_get_status_code(client)<=0;
    if (client) esp_http_client_cleanup(client);
    job->result.ok=ok;job->result.final=true;
    if (!ok && job->epoch==atomic_load(&epoch)) ESP_LOGW("muse_tts","Speech stream unavailable; retaining text reply");
    publish(job,&job->result);
    free(job);
    atomic_fetch_sub(&workers,1);
    vTaskDeleteWithCaps(NULL);
}
bool muse_reply_tts_start(const char *text,uint32_t gen,int message,uint32_t ticket) {
    if (!gadget_user_tts_url()[0] || !text || !text[0] || strlen(text)>=1024) return false;
    if (!results) results=xQueueCreateWithCaps(16,sizeof(muse_reply_tts_result_t),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
    if (!results || atomic_load(&workers)>=2) return false;
    job_t *job=heap_caps_calloc(1,sizeof(*job),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
    if (!job) return false;
    job->result.ticket=ticket;job->result.gen=gen;job->result.message=message;job->epoch=atomic_load(&epoch);
    strcpy(job->text,text);
    atomic_fetch_add(&workers,1);
    if (xTaskCreatePinnedToCoreWithCaps(run,"muse_tts",12*1024,job,4,NULL,0,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT)!=pdPASS) {
        atomic_fetch_sub(&workers,1);free(job);return false;
    }
    return true;
}
bool muse_reply_audio_start(const char *url,uint32_t gen,int message,uint32_t ticket) {
    if(!url || strlen(url)>=2048 || (strncmp(url,"http://",7) && strncmp(url,"https://",8)))return false;
    if (!results) results=xQueueCreateWithCaps(16,sizeof(muse_reply_tts_result_t),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
    if (!results || atomic_load(&workers)>=2) return false;
    job_t *job=heap_caps_calloc(1,sizeof(*job),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);if(!job)return false;
    job->native=true;strcpy(job->url,url);job->epoch=atomic_load(&epoch);
    job->result.gen=gen;job->result.message=message;job->result.ticket=ticket;
    atomic_fetch_add(&workers,1);
    if(xTaskCreatePinnedToCoreWithCaps(run,"muse_audio",12*1024,job,4,NULL,0,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT)!=pdPASS){atomic_fetch_sub(&workers,1);free(job);return false;}
    return true;
}
bool muse_reply_tts_poll(muse_reply_tts_result_t *result) {
    return results && xQueueReceive(results,result,0)==pdTRUE;
}
void muse_reply_tts_cancel(void) {atomic_fetch_add(&epoch,1);}
