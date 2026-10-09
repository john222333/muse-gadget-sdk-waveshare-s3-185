# 通用固件：下载、烧录、USB 配置

仅支持 **Waveshare ESP32-S3-LCD-1.85 无触摸 N16R8**。通用固件不含任何用户令牌、Wi-Fi 密码、家庭 IP 或配对数据。用户不用安装 ESP-IDF、不用编译；仍需自己的 Muse SDK token 和手机配对。

## 下载和安装工具

从本仓库 Releases 下载 `muse-waveshare-s3-185-flash.zip`，完整解压到短目录。保留 firmware、manifest 和工具文件的相对位置。需要 Python 3.11+，安装时可勾选加入 PATH。

Windows 双击 `install.cmd` 安装独立虚拟环境中的烧录工具。Linux/macOS：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 烧录

接好 USB 数据线、关闭串口监视器。仅接一块目标板时工具会尝试找到原生 ESP USB 端口；否则用 `--port` 明确指定。

Windows PowerShell，进入解压目录。首次替换其他固件时：

```powershell
.venv/Scripts/python.exe device.py flash --port COM3 --erase
```

**--erase 会清除旧程序、Wi-Fi、配对和全部个人配置。** COM3 是示例，换成实际端口。升级本项目且希望保留配置时，去掉 `--erase`。完整烧录包包含 bootloader、分区表、OTA 初始化数据和应用；不要把单个应用文件烧到 0。

工具先检查 manifest SHA-256，再调用 esptool 烧录，esptool 校验写入。连接不上时按住 BOOT、短按 RESET、松开 BOOT，再运行；Linux 串口访问需要相应用户组权限。

## 烧录后填写个人配置

Windows 双击 `configure.cmd`，或者：

```powershell
.venv/Scripts/python.exe device.py configure --port COM3
```

依次填写：

- **Muse SDK token**：必需；隐藏输入，首次使用必须填写自己的 token。留空仅用于保留设备已存的 token。
- **电脑 relay IPv4**：直连或路由器已提供代理时留空；电脑转发时填电脑 LAN IPv4，不填 localhost。
- **语音 API URL**：可选；留空关闭文字合成。使用本仓库主机服务时填写 `http://你的电脑LAN地址:8765/tts`。
- **语音 API Bearer key**：可选，隐藏输入；协议见[可替换语音 API](SPEECH_API.zh-CN.md)。
- **手机回复同步播放**：用于接收当前 Muse 的新助手回复，可关闭；带文字的回复使用配置的 TTS，原始 MP3/PCM16 WAV 直接播放。只同步在线连接收到的新消息，不下载历史聊天。

设置经 USB 写入设备 NVS，保存成功后重启应用。工具不向云端发送令牌、不把它写入电脑配置文件；NVS 是否加密取决于固件/设备配置，保持设备物理访问受控。

## 手机配网与联网

Muse 手机端开启 Developer mode，添加 `MuseGadget-…`，屏幕提示时短按 BOOT 确认，再按手机流程设置 2.4 GHz Wi-Fi。没有在三个按键上输入密码的步骤。

按[网络配置与验收](NETWORK_SETUP.zh-CN.md)选择直连、路由器或电脑方案。电脑 relay 必须监听 443，语音服务通常 8765；两者需要正确允许板子来源和主机防火墙规则。**USB 配置不会自动启动电脑服务、代理或设置路由器。**

电脑关机/休眠或主机服务停止会让对应功能不可用；只有直连或已配置路由器的 Muse 网络可以独立。换服务地址只需重跑 USB 配置并重启，不需重新编译/烧录。

## 如何确认包和版本

manifest 列出板型、芯片、版本、各文件地址与 SHA-256。公开包从空个人配置构建；自己的 NVS 或私人固件不在其中。源码构建方法仍保留，见[硬件与构建指南](WAVESHARE_S3_185.zh-CN.md)。

## 手机语音回复的支持范围

固件订阅当前 Muse 的消息，待机时也能接收新助手回复并唤醒播放队列。按住 BOOT 可打断并开始自己的问题。记住近期消息 ID，重发相同消息不会重复播放。板子需要在线；电池休眠/断网时不能保证接收，建议 USB 供电。

原始音频支持 MP3 和 PCM16 WAV（单/双声道，8–96 kHz，单个文件不超过 512 KB），先收完整音频再播放。有音频引用但下载或格式失败时，若带回复文字就调用配置的语音接口；没有文字时屏幕给出格式提示。AAC/Opus 等不直接解码，需要带文字的 TTS 兜底或外部转为 MP3。

本机模拟手机事件已在实际板子上验证原始 MP3/WAV 播放、下载失败后的文字兜底；实际手机 Muse 的语音事件格式仍需用用户的一条新消息复测。不能把模拟事件测试等同于所有 Muse 手机版的端到端兼容性保证。
