# 电脑语音服务与可选 TLS 转发

Python 3.11+。建议独立虚拟环境。先按[网络配置与验收](../../docs/NETWORK_SETUP.zh-CN.md)选择方案，核对固件与主机两份配置。

```sh
cd tools/muse_host
python -m venv .venv
# 激活虚拟环境后
python -m pip install -r requirements.txt
cp config.example.json config.local.json
python host.py --config config.local.json --mode all
```

Windows 可执行 `powershell -ExecutionPolicy Bypass -File setup.ps1`，然后编辑本地配置并双击 `run.cmd`。关闭终端或 Ctrl+C 停止服务。不会写入计划任务或修改系统防火墙。

## 配置

`config.local.json` 被 Git 忽略。示例默认为回环地址、只允许回环来源、未授权在线语音、未启用转发。

- `bind`：电脑实际 LAN 地址。不要把文档地址照抄到自己的网络。
- `allowed_peers`：允许的开发板及本机来源 IPv4；允许列表不能为空。
- `tts_port`：通常 8765。固件 `CONFIG_MUSE_REPLY_TTS_URL` 指向对应的 `/tts`。
- `online_speech_consent`：阅读下面的数据流说明后才改为 true。
- `speech`：音色、语速和音调，默认晓伊女声。
- `proxy`：可选 HTTP 代理 URL。留空时女声直接连接；可设置自己的 `http://127.0.0.1:端口`。
- `relay_enabled`：可选；开启时必须填写 HTTP 代理。固件 `CONFIG_MUSE_PC_RELAY_IP` 指向主机，转发端口需为 443。

代理认证暂未在 TLS relay 中实现。有认证的代理可以只用于语音，不要开启 relay。
手动设置主机防火墙：只允许开发板来源访问对应端口。不把本接口映射到公网。

## 数据流与隐私

录音通过固件正常 Muse 链路交给 Muse 识别/回答。收到的待朗读回复文本会被发送给微软在线语音服务；“不需要 API Key”不表示离线或没有第三方传输。服务启动需要显式配置 `online_speech_consent=true`。

语音服务先清除内部 UUID、追踪编号和排版标记，再生成短段语音。日志仅记录耗时、字节数和错误类型，不记录回复文本，不保存聊天音频。字幕仍由固件处理。

TLS relay 只根据 ClientHello SNI 转发 Muse 域名，使用来源允许列表，不解密设备与 Muse 之间的 TLS；它不是通用公共代理。

## 调试

- `GET /health` 返回就绪状态与音色。
- `POST /tts` 接受不超过 1024 字节的 UTF-8 纯文本。
- 有效语音返回 `audio/mpeg`；仅编号/符号返回 204，由固件直接跳过。
- 完整短段合成失败可重试一次；失败不发送部分音频，最终返回 503。
- 一次最多两个合成请求，固件用其中一个为下一段预合成。

不要把 `config.local.json`、本地固件或日志提交到公开仓库。

## 自动验证

在仓库根目录运行：

```sh
python -m unittest discover -s tools/muse_host/tests -v
python esp32/tests/test_reply_speech_pipeline.py
cc -I esp32/components/muse esp32/tests/reply_phrase_cases.c -o phrase-test
```

最后运行生成的 phrase-test（Windows 为 .exe）。固件管线测试使用 `CXX` 指定 C++17 编译器；默认 `c++`。HTTP 测试使用模拟语音，不发送文本到线上服务。

服务不会自动开机启动。电脑重启、休眠、终端关闭或代理停止后要重新启动并确认 relay/voice 各自就绪；`/health` 不是微软在线语音或 Muse 模型的验收。
