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

模型回复仍来自 Muse 云端，在线女声也不是离线模型。电脑方案需要主机和现有代理持续运行；独立路由器部署尚未完成。

## 快速开始

1. 准备 ESP-IDF **v6.0.1**、16 MB Flash / 8 MB PSRAM 的目标板，以及你自己的 Muse SDK token。
2. 按[硬件、编译与配网指南](docs/WAVESHARE_S3_185.zh-CN.md)构建、烧录及配对。
3. 如需女声，按[电脑服务指南](tools/muse_host/README.zh-CN.md)安装依赖，填写本地配置，并明确同意在线语音传输。
4. 需要代理时再开启可选 TLS 转发；无需代理可关闭。

公开配置默认只监听回环地址，在线语音未授权、TLS 转发未开启。请自行设置开发板和电脑地址。

## 文档

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
