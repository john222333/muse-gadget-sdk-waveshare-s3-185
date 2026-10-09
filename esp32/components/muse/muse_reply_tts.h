/* SPDX-FileCopyrightText: 2026 Muse Waveshare contributors
 * SPDX-License-Identifier: Apache-2.0
 */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t gen; uint32_t ticket; int message; uint8_t *audio; size_t size; bool ok; bool final; bool unavailable; } muse_reply_tts_result_t;
bool muse_reply_tts_start(const char *text, uint32_t gen, int message, uint32_t ticket);
bool muse_reply_tts_poll(muse_reply_tts_result_t *result);
void muse_reply_tts_cancel(void);
