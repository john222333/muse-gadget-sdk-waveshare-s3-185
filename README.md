# Muse Gadget SDK · Waveshare ESP32-S3-LCD-1.85

为 **Waveshare ESP32-S3-LCD-1.85 无触摸版（N16R8）**增加 Muse 语音聊天、中文屏幕和在线女声朗读的社区移植。
基于 [facebookincubator/muse-gadget-sdk](https://github.com/facebookincubator/muse-gadget-sdk)，保留上游代码与历史；不是 Meta、Waveshare 或微软的官方产品。

## 已完成

- ST77916 360×360 QSPI 圆屏、背光、电源保持和按键适配。
- 独立 I2S 麦克风/PCM5101 扬声器，确认麦克风使用右声道。
- BOOT 按住说话、松开发送，蓝牙配对与手机配置 Wi-Fi。
- 可选电脑 TLS 转发：接入现有 HTTP 代理，保留原服务器 TLS 认证。
- 微软在线晓伊女声，无需自行填写语音 API Key；每段确认完整后发送，支持一次重试、下一段预合成和对话打断。
- 修复空行造成后续不朗读、单句截断、尾句遗漏、末尾读出 UUID/内部编号等问题。
- 完整中文说明、公开配置模板、测试与验证记录。

模型回复仍来自 Muse 云端，在线女声也不是离线模型。电脑转发方案需要主机和现有代理持续运行，女声需要语音主机；独立路由器部署尚未完成。

## 直接烧录

提供 **0.2.0 通用烧录包**：[下载 Releases](https://github.com/john222333/muse-gadget-sdk-waveshare-s3-185/releases)。用户不用安装 ESP-IDF 或编译；固件没有内置私人令牌，烧录后用 USB 填写自己的 Muse SDK token，再用手机配网/配对。

1. 下载 `muse-waveshare-s3-185-flash.zip`，解压并安装 Python 3.11+，运行 `install.cmd`。
2. 按[直接烧录指南](docs/DIRECT_FLASH.zh-CN.md)烧录正确的无触摸 N16R8 板子，运行 `configure.cmd` 填写个人参数。
3. Muse 手机端开启 Developer mode，添加设备，短按 BOOT 确认，再选择 2.4 GHz Wi-Fi。
4. 按[网络配置与验收](docs/NETWORK_SETUP.zh-CN.md)选择直连、路由器或电脑转发；电脑服务与防火墙不会自动配置。
5. 如需文字朗读，可使用[自己的语音 API](docs/SPEECH_API.zh-CN.md)，或[可选电脑微软女声服务](tools/muse_host/README.zh-CN.md)。接口地址与 Bearer key 可在烧录后更改。

手机新助手回复可同步到待机板子：MP3/PCM16 WAV 直接播放；带文字时可由自选接口朗读。支持范围和实测界限见直接烧录指南，不保证所有手机端事件格式。源代码构建方法保留在[硬件指南](docs/WAVESHARE_S3_185.zh-CN.md)。

## 文档

- [直接烧录与 USB 配置](docs/DIRECT_FLASH.zh-CN.md)
- [可替换语音 API](docs/SPEECH_API.zh-CN.md)
- [网络配置、端口、防火墙和逐步验收](docs/NETWORK_SETUP.zh-CN.md)
- [硬件、编译、配网和操作](docs/WAVESHARE_S3_185.zh-CN.md)
- [前期工作总结与修复过程](docs/WORK_SUMMARY.zh-CN.md)
- [验证结果、耗时和限制](docs/VALIDATION.zh-CN.md)
- [电脑服务与隐私说明](tools/muse_host/README.zh-CN.md)
- [上游项目原始说明](README.upstream.md)
- [许可与第三方来源](THIRD_PARTY_NOTICES.md)

## 测试

```sh
python -m pip install -r tools/muse_host/requirements.txt
python -m unittest discover -s tools/muse_host/tests -v
python -m unittest discover -s esp32/tests -p 'test_reply_speech*.py' -v
```

第二项固件逻辑测试需要 C++17 编译器。原有协议和硬件测试方法见 `esp32/AGENTS.md`。

## 开源范围

公开源码、配置示例、说明和测试；不包含 SDK token、Wi-Fi/路由器密码、个人网络地址、用户对话日志、配对数据、烧录备份或带个人配置的固件。重新编译时使用你自己的本地配置。

代码沿用 **Apache-2.0**，第三方文件和运行依赖保留各自许可。在线服务、模型和音色没有因此变成开源或获得永久可用承诺。
