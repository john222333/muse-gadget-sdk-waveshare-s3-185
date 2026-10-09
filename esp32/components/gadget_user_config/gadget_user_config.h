/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include "esp_err.h"
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif
esp_err_t gadget_user_config_init(void);
const char *gadget_user_sdk_token(void);
const char *gadget_user_tts_url(void);
const char *gadget_user_tts_key(void);
const char *gadget_user_relay_ip(void);
bool gadget_user_phone_audio(void);
/* Saves validated fields. Reboot applies them; never returns credentials. */
esp_err_t gadget_user_config_save(const char *json);
#ifdef __cplusplus
}
#endif
