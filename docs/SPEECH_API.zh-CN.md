# 可替换语音 API

通用固件不内置微软、火山引擎或其他服务商的私人凭据。烧录后通过 USB 配置 `tts_url` 和可选 `tts_key`，重启生效；之后更换服务无需重新烧录。留空 `tts_url` 表示关闭文字合成朗读。

## 板子接口协议

| 项目 | 约定 |
|---|---|
| 请求 | POST 到完整 `tts_url`，HTTP 或 HTTPS |
| 请求头 | `Content-Type: text/plain; charset=utf-8` |
| 请求正文 | 待朗读 UTF-8 文字，不超过 1023 字节；没有 JSON 包装 |
| 可选授权 | 配置 `tts_key` 后发送 `Authorization: Bearer <key>` |
| 成功 | HTTP 200，`Content-Type: audio/mpeg`，正文为 MP3 字节 |
| 不需朗读 | HTTP 204，零字节，板子跳过 |
| 失败 | 非 200/204；板子保留文字，不把错误 JSON 当音频播放 |
| HTTPS | 校验服务器证书；自签名证书未加入信任库时不能直接使用 |
| 传输 | 支持 Content-Length 或正确结束的 chunked 响应；单段上限 512 KB |
| 超时 | 板子 HTTP 请求 15 秒，服务应在此之前完成 |

API key 最长 191 字节，URL 最长 255 字节。不要把 key 放在公开配置或 URL 查询参数里。需要授权的远程接口用 HTTPS；HTTP 仅用于可信局域网中的服务。

## 接自己的声音

如果你选择的服务直接支持上述协议，填写完整接口即可。很多服务商接收 JSON、要求模型/音色参数，或返回 WAV/PCM/音频下载 URL；这些接口不能直接填给板子，需要在自己的电脑/服务器做一个适配服务：

1. `/tts` 接收板子的纯文字。
2. 适配服务按服务商官方协议调用，服务商 API key 保留在适配服务本地。
3. 把结果转换/请求为 MP3，返回 `audio/mpeg`；JSON、WAV、PCM 不能冒充 MP3。
4. 每个短段完整生成后再发布给板子，避免失败时播放半句话；可在适配端重试一次。
5. 固件配置适配服务的 URL，若适配服务自己需要鉴权，再设置 `tts_key`。

本仓库 `tools/muse_host/voice_bridge.py` 是符合该协议的可选微软在线实现。可以替换它的 `synthesize`，保持 HTTP 契约与异常处理。它默认没有实现 Bearer 校验，依靠来源允许列表；若要部署远程 API，应在自己的服务端验证授权。

选择线上音色会把朗读文字交给相应服务商；选择本地离线合成时由自己的适配服务决定数据是否出网。原有微软 voice 服务仍要求 `online_speech_consent=true`。

## 配置示例

USB 交互配置工具会分别询问地址和隐藏输入的 key；不把个人配置保存到电脑文件，也不在设备应答中回显 key。开发人员也可通过串口发送以下命令（示例无实际 key）：

```text
>user.config={"tts_url":"https://voice.example.com/tts","tts_key":"","phone_audio":true}
>user.reboot
```

这只改变语音设置，不清除 Wi-Fi 或配对。更换 Muse SDK token 可能还需要在手机里重新配对；SDK token 和语音 API key 是不同字段。
