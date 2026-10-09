/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Waveshare ESP32-S3-LCD-1.85, no touch, N16R8, native USB 303a:1001.
 * Pin maps and LCD revision table: vendor ESP32-S3-LCD-1.85-Demo.zip,
 * ESP-IDF/.../main/{LCD_Driver,EXIO,I2C_Driver,MIC_Driver,Audio_Driver,PWR_Key}.
 * Microphone and PCM5101 use separate I2S controllers and clock pins.
 * Touch GPIOs are deliberately untouched on this no-touch board.
 */
#include <math.h>
#include <limits.h>
#include "driver/i2c_master.h"
#include "driver/i2s_std.h"
#include "driver/ledc.h"
#include "driver/spi_master.h"
#include "driver/usb_serial_jtag.h"
#include "esp_check.h"
#include "esp_codec_dev.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_st77916.h"
#include "esp_lv_adapter.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "muse_audio.h"
#include "muse_board.h"
#include "muse_mem.h"
#include "waveshare_s3_185_lcd_init.h"

static const char *TAG = "board_185";
static i2c_master_bus_handle_t s_i2c;
static i2c_master_dev_handle_t s_exio;
static esp_lcd_panel_handle_t s_panel;
static muse_gpio_button_t s_talk, s_aux;
static i2s_chan_handle_t s_tx, s_rx;
static int32_t s_mic_dc[2];
static int s_mic_gain_q8 = 256;

static esp_err_t exio_write(uint8_t reg, uint8_t value)
{
    uint8_t bytes[] = {reg, value};
    return i2c_master_transmit(s_exio, bytes, sizeof(bytes), 100);
}

static esp_err_t init(void)
{
    const gpio_config_t power = {.pin_bit_mask=1ULL<<7, .mode=GPIO_MODE_OUTPUT};
    ESP_RETURN_ON_ERROR(gpio_config(&power), TAG, "power latch");
    gpio_set_level(7, 1);
    const i2c_master_bus_config_t bus = {
        .i2c_port=I2C_NUM_0, .sda_io_num=GPIO_NUM_11, .scl_io_num=GPIO_NUM_10,
        .clk_source=I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt=7,
        .flags.enable_internal_pullup=true,
    };
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&bus, &s_i2c), TAG, "i2c");
    const i2c_device_config_t dev = {
        .dev_addr_length=I2C_ADDR_BIT_LEN_7, .device_address=0x20, .scl_speed_hz=400000,
    };
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(s_i2c, &dev, &s_exio), TAG, "TCA9554");
    /* Only EXIO2 is driven: LCD reset. Keep all other expander lines inputs. */
    uint8_t reg=1, outputs=0;
    ESP_RETURN_ON_ERROR(i2c_master_transmit_receive(s_exio, &reg, 1, &outputs, 1, 100), TAG, "expander latch");
    ESP_RETURN_ON_ERROR(exio_write(1, outputs & ~2), TAG, "LCD reset low");
    ESP_RETURN_ON_ERROR(exio_write(3, 0xfd), TAG, "LCD reset output");
    vTaskDelay(pdMS_TO_TICKS(10));
    ESP_RETURN_ON_ERROR(exio_write(1, outputs | 2), TAG, "LCD reset high");
    vTaskDelay(pdMS_TO_TICKS(50));
    ESP_RETURN_ON_ERROR(muse_gpio_button_init(&s_talk, GPIO_NUM_0),TAG,"BOOT");
    return muse_gpio_button_init(&s_aux, GPIO_NUM_6);
}

static lv_display_t *display_start(lv_indev_t **touch)
{
    *touch=NULL;
    const ledc_timer_config_t timer = {
        .speed_mode=LEDC_LOW_SPEED_MODE, .duty_resolution=LEDC_TIMER_10_BIT,
        .timer_num=LEDC_TIMER_0, .freq_hz=5000, .clk_cfg=LEDC_AUTO_CLK,
    };
    const ledc_channel_config_t light = {
        .gpio_num=5, .speed_mode=LEDC_LOW_SPEED_MODE, .channel=LEDC_CHANNEL_0,
        .timer_sel=LEDC_TIMER_0, .duty=0,
    };
    if (ledc_timer_config(&timer)!=ESP_OK || ledc_channel_config(&light)!=ESP_OK) return NULL;
    /* Two 12-row draw buffers save 28.8 KB of internal RAM versus 32 rows.
     * Pairing needs a contiguous 8 KB provisioning stack plus TLS allocations. */
    const spi_bus_config_t bus = {
        .sclk_io_num=40, .data0_io_num=46, .data1_io_num=45,
        .data2_io_num=42, .data3_io_num=41,
        .data4_io_num=-1, .data5_io_num=-1, .data6_io_num=-1, .data7_io_num=-1,
        .max_transfer_sz=360*12*2,
    };
    if (spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO)!=ESP_OK) return NULL;
    esp_lcd_panel_io_handle_t probe_io, io;
    esp_lcd_panel_io_spi_config_t io_cfg = {
        .cs_gpio_num=21, .dc_gpio_num=-1, .spi_mode=0, .pclk_hz=3000000,
        .trans_queue_depth=10, .lcd_cmd_bits=32, .lcd_param_bits=8,
        .flags.quad_mode=true,
    };
    if (esp_lcd_new_panel_io_spi(SPI2_HOST, &io_cfg, &probe_io)!=ESP_OK) return NULL;
    uint8_t id[4]={0};
    esp_err_t probe=esp_lcd_panel_io_rx_param(probe_io, (0x0b<<24)|(0x04<<8), id, sizeof(id));
    esp_lcd_panel_io_del(probe_io);
    ESP_LOGI(TAG, "LCD ID: %02x %02x %02x %02x (probe %s)", id[0],id[1],id[2],id[3],esp_err_to_name(probe));
    /* Conservative 40 MHz QSPI clock. Vendor example uses 80 MHz. */
    io_cfg.pclk_hz=40000000;
    if (esp_lcd_new_panel_io_spi(SPI2_HOST, &io_cfg, &io)!=ESP_OK) return NULL;
    st77916_vendor_config_t vendor = {.flags.use_qspi_interface=true};
    if (probe==ESP_OK && id[0]==0 && id[1]==2 && id[2]==0x7f && id[3]==0x7f) {
        vendor.init_cmds=vendor_specific_init_new;
        vendor.init_cmds_size=sizeof(vendor_specific_init_new)/sizeof(vendor_specific_init_new[0]);
    }
    const esp_lcd_panel_dev_config_t panel = {
        .reset_gpio_num=-1, .rgb_ele_order=LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel=16, .vendor_config=&vendor,
    };
    if (esp_lcd_new_panel_st77916(io, &panel, &s_panel)!=ESP_OK) return NULL;
    if (esp_lcd_panel_reset(s_panel)!=ESP_OK || esp_lcd_panel_init(s_panel)!=ESP_OK ||
        esp_lcd_panel_disp_on_off(s_panel,true)!=ESP_OK) return NULL;
    esp_lv_adapter_config_t cfg=ESP_LV_ADAPTER_DEFAULT_CONFIG();
    cfg.task_core_id=MUSE_UI_CORE;
    cfg.task_priority=MUSE_UI_PRIORITY;
    if (esp_lv_adapter_init(&cfg)!=ESP_OK) return NULL;
    const esp_lv_adapter_display_config_t disp_cfg = {
        .panel=s_panel, .panel_io=io,
        .profile={.interface=ESP_LV_ADAPTER_PANEL_IF_OTHER, .rotation=ESP_LV_ADAPTER_ROTATE_0,
            .hor_res=360, .ver_res=360, .buffer_height=12, .use_psram=false,
            .require_double_buffer=true},
        .tear_avoid_mode=ESP_LV_ADAPTER_TEAR_AVOID_MODE_NONE,
    };
    lv_display_t *disp=esp_lv_adapter_register_display(&disp_cfg);
    if (!disp || esp_lv_adapter_start()!=ESP_OK) return NULL;
    return disp;
}

static bool display_lock(int timeout_ms) {return esp_lv_adapter_lock(timeout_ms)==ESP_OK;}
static void set_brightness(int pct)
{
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, pct*1023/100);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}
static void panel_sleep(bool sleep) {esp_lcd_panel_disp_sleep(s_panel,sleep);}
static int data_enable(const audio_codec_data_if_t *h, esp_codec_dev_type_t type, bool on)
{(void)h;(void)type;(void)on;return ESP_CODEC_DEV_OK;}
static int spk_write(const audio_codec_data_if_t *h, uint8_t *data, int size)
{
    (void)h; size_t wrote=0;
    return i2s_channel_write(s_tx,data,size,&wrote,portMAX_DELAY)==ESP_OK && wrote==(size_t)size
        ? ESP_CODEC_DEV_OK : ESP_CODEC_DEV_WRITE_FAIL;
}
static int mic_read(const audio_codec_data_if_t *h, uint8_t *data, int size)
{
    (void)h; size_t got=0;
    if (i2s_channel_read(s_rx,data,size,&got,pdMS_TO_TICKS(1000))!=ESP_OK || got!=(size_t)size)
        return ESP_CODEC_DEV_READ_FAIL;
    int16_t *samples=(int16_t *)data;
    for(int i=0;i<size/2;i++) {
        int32_t *dc=&s_mic_dc[i&1];
        *dc+=(samples[i]*256-*dc)>>8;
        int v=(samples[i]-(*dc>>8))*s_mic_gain_q8>>8;
        samples[i]=v>INT16_MAX?INT16_MAX:v<INT16_MIN?INT16_MIN:v;
    }
    return ESP_CODEC_DEV_OK;
}
static void set_mic_gain(esp_codec_dev_handle_t mic,int db)
{(void)mic; s_mic_gain_q8=(int)(256.0f*powf(10.0f,db/20.0f));}
static esp_err_t audio_init(esp_codec_dev_handle_t *spk,esp_codec_dev_handle_t *mic)
{
    i2s_chan_config_t tx_cfg=I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0,I2S_ROLE_MASTER);
    tx_cfg.auto_clear=true;
    ESP_RETURN_ON_ERROR(i2s_new_channel(&tx_cfg,&s_tx,NULL),TAG,"speaker channel");
    i2s_chan_config_t rx_cfg=I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1,I2S_ROLE_MASTER);
    ESP_RETURN_ON_ERROR(i2s_new_channel(&rx_cfg,NULL,&s_rx),TAG,"mic channel");
    i2s_std_config_t tx={
        .clk_cfg=I2S_STD_CLK_DEFAULT_CONFIG(MUSE_AUDIO_RATE),
        .slot_cfg=I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO),
        .gpio_cfg={.mclk=I2S_GPIO_UNUSED,.bclk=GPIO_NUM_48,.ws=GPIO_NUM_38,
            .dout=GPIO_NUM_47,.din=I2S_GPIO_UNUSED},
    };
    i2s_std_config_t rx={
        .clk_cfg=I2S_STD_CLK_DEFAULT_CONFIG(MUSE_AUDIO_RATE),
        .slot_cfg=I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO),
        .gpio_cfg={.mclk=I2S_GPIO_UNUSED,.bclk=GPIO_NUM_15,.ws=GPIO_NUM_2,
            .dout=I2S_GPIO_UNUSED,.din=GPIO_NUM_39},
    };
    rx.slot_cfg.slot_bit_width=I2S_SLOT_BIT_WIDTH_32BIT;
    rx.slot_cfg.ws_width=32;
    ESP_RETURN_ON_ERROR(i2s_channel_init_std_mode(s_tx,&tx),TAG,"speaker config");
    ESP_RETURN_ON_ERROR(i2s_channel_init_std_mode(s_rx,&rx),TAG,"mic config");
    ESP_RETURN_ON_ERROR(i2s_channel_enable(s_tx),TAG,"speaker on");
    ESP_RETURN_ON_ERROR(i2s_channel_enable(s_rx),TAG,"mic on");
    static const audio_codec_data_if_t spk_if={.enable=data_enable,.write=spk_write};
    static const audio_codec_data_if_t mic_if={.enable=data_enable,.read=mic_read};
    esp_codec_dev_cfg_t out={.dev_type=ESP_CODEC_DEV_TYPE_OUT,.data_if=&spk_if};
    esp_codec_dev_cfg_t in={.dev_type=ESP_CODEC_DEV_TYPE_IN,.data_if=&mic_if};
    *spk=esp_codec_dev_new(&out); *mic=esp_codec_dev_new(&in);
    return *spk && *mic ? ESP_OK : ESP_FAIL;
}
static unsigned poll_buttons(void) {return muse_gpio_button_poll(&s_talk) | (muse_gpio_button_poll(&s_aux)<<2);}
static esp_err_t power_off(void)
{
    set_brightness(0);
    esp_lcd_panel_disp_on_off(s_panel,false);
    while(gpio_get_level(GPIO_NUM_0)==0) vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(7,0);
    ESP_RETURN_ON_ERROR(esp_sleep_enable_ext0_wakeup(GPIO_NUM_0,0),TAG,"wake");
    esp_deep_sleep_start(); return ESP_FAIL;
}
static const muse_board_t s_board={
    .name="Waveshare ESP32-S3-LCD-1.85 (no touch)", .width=360,.height=360,
    .round=true,.touch=false,.diagonal_in=1.85f,.talk_button="boot",
    .aux_button="power",.aux_hint={LV_ALIGN_TOP_MID,0,12},
    .talk_hint={LV_ALIGN_BOTTOM_MID,0,-12},.frame_ms=40,
    .init=init,.display_start=display_start,.display_lock=display_lock,
    .display_unlock=esp_lv_adapter_unlock,.set_brightness=set_brightness,.panel_sleep=panel_sleep,
    .audio_init=audio_init,.mic_slot=1,.set_mic_gain=set_mic_gain,
    .poll_buttons=poll_buttons,.power_off=power_off,
};
const muse_board_t *muse_board_get(void) {return &s_board;}
