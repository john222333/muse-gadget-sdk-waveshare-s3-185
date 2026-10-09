# 硬件、编译和使用

## 支持的板子

Waveshare **ESP32-S3-LCD-1.85，无触摸版**。已验证 ESP32-S3 N16R8：16 MB Flash、8 MB octal PSRAM、360×360 ST77916 QSPI LCD、I2S 麦克风、PCM5101 扬声器。
不要直接套用到 1.85C、带触摸或其他接线的型号。

| 功能 | 接线 |
|---|---|
| LCD QSPI CLK / D0 / D1 / D2 / D3 | GPIO40 / 46 / 45 / 42 / 41 |
| LCD CS / 背光 | GPIO21 / GPIO5 |
| I2C SDA / SCL | GPIO11 / GPIO10 |
| TCA9554 / LCD 复位 | I2C 0x20 / EXIO2 |
| 扬声器 BCLK / WS / DATA | GPIO48 / 38 / 47，I2S0 |
| 麦克风 BCLK / WS / DATA | GPIO15 / 2 / 39，I2S1，右声道 |
| BOOT / PWR / 电源保持 | GPIO0 / GPIO6 / GPIO7 |

硬件事实参考 [Waveshare 官方资料](https://www.waveshare.com/wiki/ESP32-S3-LCD-1.85)及厂家公开 Demo 的 LCD、EXIO、I2C、MIC、Audio、PWR 示例。未初始化触摸控制器。

## 新用户先读

[网络配置与验收](NETWORK_SETUP.zh-CN.md)说明源码发布的前提，以及直连、路由器代理、电脑转发三种方案。0.2.0 通用包按[直接烧录指南](DIRECT_FLASH.zh-CN.md)使用；下面方法供源码构建。

## 编译

激活 ESP-IDF **v6.0.1**。进入 `esp32`，复制 `sdkconfig.local.example` 为 `sdkconfig.local`，只在本机填入自己的 `CONFIG_GADGET_SDK_TOKEN`。本地文件已被忽略，不提交。

需要女声时填写 `CONFIG_MUSE_REPLY_TTS_URL="http://你的电脑地址:8765/tts"`；需要 TLS 代理转发时填写 `CONFIG_MUSE_PC_RELAY_IP="你的电脑地址"`。两项默认空，保留正常 DNS/无外部朗读。

```sh
idf.py -B build-s3-185 -DIDF_TARGET=esp32s3 -DSDKCONFIG=build-s3-185/sdkconfig -DSDKCONFIG_DEFAULTS="sdkconfig.defaults;devices/sdkconfig.muse;devices/sdkconfig.muse-waveshare-s3-185;sdkconfig.local" build
idf.py -B build-s3-185 -p YOUR_SERIAL_PORT flash
```

命令以一行形式列出，适用于 POSIX shell 和 PowerShell。本页手动命令会明确加载 `sdkconfig.local`。`tools/muse/board.sh` 当前不会自动加载该文件，新用户请使用本页命令，避免遗漏令牌或服务地址。

首次从其他固件迁移时，用以下命令先清空 Flash，再完整烧录；**会删除旧程序、Wi-Fi 与配对信息**。将 YOUR_SERIAL_PORT 换成实际端口（Windows 如 COM3，Linux 如 /dev/ttyACM0）。已经用本项目配对的升级无需清空：正常 `flash` 保留 NVS。不要只把应用 bin 烧到地址 0。

```sh
idf.py -B build-s3-185 -p YOUR_SERIAL_PORT erase-flash
idf.py -B build-s3-185 -p YOUR_SERIAL_PORT flash monitor
```

烧录连接不上时按住 BOOT、短按 RESET、松开 BOOT，再尝试。monitor 用 Ctrl+] 退出。不要直接写死别人板子的端口。

已有生成 sdkconfig 会优先于默认配置。更改 `sdkconfig.local` 后用新目录构建（同时更改 `-B` 和 `-DSDKCONFIG` 的路径），或运行 `idf.py -B build-s3-185 -DSDKCONFIG=build-s3-185/sdkconfig menuconfig` 修改对应选项，再 build/flash。

本移植关闭 OTA；开发签名方式沿用上游。不要把上游公开开发签名密钥当成生产私钥。

## 配对和按键

- Muse 手机端开启 `Settings > Devices > Developer mode`，在 Devices 的 + 添加 `MuseGadget-…`；屏幕提示确认配对时短按 BOOT，再按手机流程选择 2.4 GHz Wi-Fi 和输入密码。
- BOOT 按住说话、松开发送；回复播放时再次按住可以打断并开始下一轮。
- PWR 是辅助菜单键，BOOT 配合选择；RESET 是重启，不是触摸或音量键。
- 没有触摸屏，Wi-Fi 不是在三个按键上输入。

## 排障

- 输入 Wi-Fi 后一直转：检查 2.4 GHz、密码、手机蓝牙权限和板子启动日志。
- 有字幕没语音：检查主机服务、`online_speech_consent`、开发板 TTS URL、允许的来源地址、扬声器设置和防火墙。
- 直连 Muse 不通：可启用电脑转发；电脑必须能通过现有代理访问 Muse。
- 一句话中断：检查完整段重试和网络停顿；当前实现不会把未合成完整的片段先发出。
- 云端很久不回答：区分松手→Muse 首段文字与合成→播放；后者快不代表模型阶段也快。
- 主机地址变化：更新本地配置和固件服务地址，或自行配置固定 DHCP 租约。

串口输入 `t` 可播放固定的三段测试语音，并验证空行、排版符号和末尾内部编号跳过；输入 `m` 为上游 MP3 测试。
