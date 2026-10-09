# License and provenance

- Base project: Meta Platforms, Inc. and affiliates, [facebookincubator/muse-gadget-sdk](https://github.com/facebookincubator/muse-gadget-sdk), base commit `86cf33fb4092ba700b4dc33928966d1bcb31556d`; Apache-2.0. Existing notices are retained.
- ST77916 driver (`esp_lcd_st77916.c/.h`): original Espressif Systems (Shanghai) CO LTD notices and Apache-2.0 SPDX headers are retained.
- LCD register configuration and board pin facts were checked against the public [Waveshare ESP32-S3-LCD-1.85 documentation and demo](https://www.waveshare.com/wiki/ESP32-S3-LCD-1.85). The vendor demo archive is not redistributed.
- MP3 decoder: upstream minimp3, CC0-1.0, with its included LICENSE. Other upstream bundled fonts/components keep their existing notices.
- Host runtime dependency [edge-tts](https://github.com/rany2/edge-tts) 7.2.8: LGPLv3; installed separately, not vendored. The host adapter sets a public aiohttp WebSocket close-timeout argument; it does not ship an edited copy of edge-tts.
- [aiohttp](https://github.com/aio-libs/aiohttp) 3.14.4: Apache-2.0; installed separately. Transitive dependencies retain their own licenses.
- ESP-IDF and managed components downloaded during build are covered by their own licenses.

Added implementation and documentation are distributed under Apache-2.0. Modified upstream files retain original notices; this project is a community derivative, not an official release from Meta, Waveshare or Microsoft.

No Microsoft voice assets, Jianying voices, personal SDK credentials or provisioned firmware binaries are distributed. Open-source code does not grant rights to external models, accounts or hosted voice services. The upstream development signing key was already public; it is a development fixture, not a private credential of the user.

## Public 0.2.0 firmware bundle

The release includes a generic, unprovisioned firmware build, not a user's flash/NVS dump. Added code uses Apache-2.0; dependency licenses remain applicable. The bundle includes license texts for ESP-IDF, managed components, minimp3 and fonts.

GNU Unifont 16.0.04 CJK bitmaps are by Roman Czyborra, Paul Hardy and contributors, distributed here under SIL OFL 1.1 (see `third_party_licenses/Unifont-OFL-1.1.txt` and `esp32/components/muse/fonts/README.md`). Existing unscii, LVGL/Adafruit fonts retain their original notices.

Upstream Jollybot artwork is explicitly excluded from the upstream Apache license (see `README.upstream.md`). The source fork retains those notices; the generic Waveshare firmware uses the original Apache-licensed community pixel avatar instead.

The USB installer separately installs esptool 5.4.0 (GPL-2.0-or-later) and pyserial 3.5 (BSD-3-Clause). Their package license notices apply; no installer dependency is vendored in the ZIP.
