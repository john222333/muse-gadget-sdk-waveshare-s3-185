# 从首次烧录到联网：配置与验收

## 能否下载后直接烧录就互联？

**0.2.0 提供通用烧录包，不需要用户自行编译。** 按[直接烧录指南](DIRECT_FLASH.zh-CN.md)下载、烧录，通过 USB 填写自己的 Muse SDK token 和服务地址，再用手机配置 Wi-Fi 并配对。没有内置账号或 Wi-Fi 密码，烧录本身不会完成云端账号绑定。

本页 `sdkconfig.local` 示例用于源码构建。通用固件直接在 USB 配置工具填写：`CONFIG_GADGET_SDK_TOKEN` 对应 `sdk_token`，`CONFIG_MUSE_PC_RELAY_IP` 对应 `relay_ip`，`CONFIG_MUSE_REPLY_TTS_URL` 对应 `tts_url`。NVS 保存的运行时值优先于编译默认值，更换服务地址后保存并重启，无需重编译。

这里的互联指开发板与 Muse 建立连接、发起语音问题和接收回复。任意智能家居设备自动发现/控制不在本次验收范围内。

| 想实现的功能 | 烧录之外还需要什么 | 电脑能否关机 |
|---|---|---|
| 板子直连 Muse，发送语音并显示回复 | Muse 账号/有效 SDK token、手机端配对、能访问 Muse 的 2.4 GHz 网络 | 配对完成后可以，须关闭固件电脑转发选项 |
| 经已配置代理的路由器访问 Muse | 上述账号/配对条件，路由器真正为板子的流量提供代理 | 网络可独立；路由器具体部署未由本项目验收 |
| 经电脑代理访问 Muse | 固件转发地址、电脑 TLS relay、HTTP 代理、局域网通路 | 不可以 |
| 晓伊女声读出回复 | 固件 TTS 地址、电脑 voice 服务、微软服务可达、在线语音同意 | 不可以；即使 Muse 网络走路由器，也仍需 TTS 主机 |

无需语音 API Key，仅适用于当前在线女声实现；**Muse SDK token 仍然必需**。默认配置没有开启电脑转发或在线朗读。

## 首次使用前准备

1. 确认是 Waveshare ESP32-S3-LCD-1.85 **无触摸 N16R8**，用 USB 数据线，不套用其他板型。
2. 使用通用包时安装 Python 3.11+ 与包内工具；只有源码构建才需要安装并激活 ESP-IDF **v6.0.1**。按上游 [ESP32 安装说明](../esp32/README.md)准备工具链；Windows 建议短源码路径，减少依赖文件路径过长问题。
3. 登录 [Muse SDK token 页面](https://gadgets.muse.ai/settings/sdk-tokens)，获取自己的 token，阅读 [SDK 条款](https://gadgets.muse.ai/sdk-terms)。Muse 手机端及账号的可用性由服务提供方决定。
4. 准备正常 DHCP/DNS 的 2.4 GHz Wi-Fi。手机蓝牙开启，允许 Muse 使用蓝牙及系统要求的附近设备权限。首次配对让手机、板子靠近。
5. 选择下面 A/B/C 网络方案，再通过 USB 保存服务地址（源码构建也可设置默认值）。Wi-Fi 密码在手机配网时填写，不写进公开源码。

## A. 网络能直接访问 Muse

本机 `esp32/sdkconfig.local`：

```ini
CONFIG_GADGET_SDK_TOKEN="填入自己的SDK令牌"
CONFIG_MUSE_PC_RELAY_IP=""
CONFIG_MUSE_REPLY_TTS_URL=""
```

板子通过路由器的 DHCP/DNS 和互联网连接 Muse。仅电脑上的浏览器可以访问，不足以证明板子可直连；浏览器可能用了电脑代理。

需要女声时，将 TTS URL 改成下面 C 中的电脑地址，安装 voice 服务；`CONFIG_MUSE_PC_RELAY_IP` 仍留空，`relay_enabled` 仍为 false。这样 Muse 网络不经过电脑，朗读才经过电脑。

## B. 路由器提供代理

固件 `CONFIG_MUSE_PC_RELAY_IP=""`，板子使用路由器正常提供的网络。路由器必须实际代理板子到 Muse 的流量，单纯在路由器里保存订阅不代表生效；只代理浏览器/单台电脑也不代表板子能用。

确认板子使用的网关/DNS和路由策略，没有被访客网、VLAN 或 IPv6 分流绕开。具体参数依路由器的代理实现而定，本项目没有交付或验证任何特定路由器的独立部署脚本。可先按 C 使用电脑，避免把未验证路由器方案当成已完成。

## C. 电脑转发 Muse，并提供女声

下面是一组**虚构示例地址**，必须全部换成自己网络的地址：电脑 `192.168.50.10`、板子 `192.168.50.20`。电脑可用有线连接，板子用 Wi-Fi；两者必须能直接互通。关闭无线 AP/客户端隔离，避开访客网；跨网段时自行配置路由和防火墙。

Windows 在 `ipconfig` 找连接家庭路由器的 IPv4，别选 VPN、虚拟网卡、169.254 地址。板子地址从路由器客户端列表/启动日志获取；建议为电脑和板子设置固定 DHCP 租约，避免重启后地址变化。

**两份配置必须对应：**

`esp32/sdkconfig.local`（编译进固件）：

```ini
CONFIG_GADGET_SDK_TOKEN="填入自己的SDK令牌"
CONFIG_MUSE_PC_RELAY_IP="192.168.50.10"
CONFIG_MUSE_REPLY_TTS_URL="http://192.168.50.10:8765/tts"
```

`tools/muse_host/config.local.json`（电脑本地文件）：

```json
{
  "bind": "192.168.50.10",
  "allowed_peers": ["192.168.50.20", "192.168.50.10"],
  "tts_port": 8765,
  "relay_port": 443,
  "relay_enabled": true,
  "proxy": "http://127.0.0.1:7890",
  "online_speech_consent": true,
  "speech": {"voice": "zh-CN-XiaoyiNeural", "rate": "-5%", "pitch": "+2Hz"}
}
```

- `7890` 是示例，换成代理软件实际的 **HTTP 或混合端口**。只支持 SOCKS 的端口不能直接填入；relay 的代理认证尚未实现。
- 代理的 `127.0.0.1` 指电脑自己；板子 TTS/relay 必须使用电脑 LAN 地址，不能用 `localhost` 或 `127.0.0.1`。
- `bind` 不能保留默认回环地址，否则板子无法访问。`allowed_peers` 包括板子，示例额外包含电脑自身方便本机验收；地址变化要同步更新。
- relay 入站端口必须是 **443**：固件只替换 Muse 域名解析地址，不改端口。TTS 是 HTTP **8765**，二者不可互换。443 已占用时先检查其他服务；不是随便换 relay_port 就能解决。
- `online_speech_consent=true` 表示同意把待朗读回复文本交给微软；不同意就不要启动 voice，不配置 TTS URL。

首次按 [主机安装指南](../tools/muse_host/README.zh-CN.md)安装。按顺序启动：**代理软件 → relay → voice → 板子联网**。可在两个终端分别运行，便于确认两个服务都启动成功：

```sh
cd tools/muse_host
.venv/Scripts/python.exe host.py --config config.local.json --mode relay
```

第二个终端：

```sh
cd tools/muse_host
.venv/Scripts/python.exe host.py --config config.local.json --mode voice
```

Windows 也可在配置完成后双击 `run.cmd` 同时启动。POSIX 系统将 `.venv/Scripts/python.exe` 换为 `.venv/bin/python`。relay 模式不要求在线语音同意，voice 模式要求。

**本项目没有安装开机自启动。** 电脑关机/休眠、终端关闭、代理停止都会使相关功能失效。重启电脑后要重新启动这些服务。启动成功时分别出现 `encrypted relay listening` 和 `reply speech ready`；不能仅看代理软件图标。

## 网络端口与去向

| 连接 | 协议/端口 | 需要的配置 |
|---|---|---|
| 手机 → 板子首次配对 | BLE | 手机权限，屏幕提示后 BOOT 确认；不要求路由器公网端口映射 |
| 板子 → 路由器 | 2.4 GHz Wi-Fi / DHCP / DNS | SSID/密码，正常网关与 DNS |
| 板子 → Muse（A/B） | TLS/HTTPS 443，含持续连接 | `api.muse.ai`、`hatch.metaaivm.com` 及配对返回的服务主机；代码覆盖 `muse.ai`/`metaaivm.com` 域名树 |
| 板子 → 电脑 relay（C） | 原始 TLS/TCP 443 | 固件 relay IP、电脑监听地址、来源允许列表、入站防火墙 |
| 电脑 relay → 本机代理 → Muse | HTTP CONNECT → TLS 443 | HTTP 代理端口正确，支持 CONNECT/长连接，代理能访问 Muse |
| 板子 → 电脑 voice | HTTP/TCP 8765 `/tts` | 固件完整 URL、voice 监听地址、来源允许列表、入站防火墙 |
| 电脑 voice → 微软 | HTTPS/WSS 443 | 当前依赖使用 `speech.platform.bing.com`，可直连或走 config 中的 HTTP 代理 |

路由器/防火墙应允许正常 DNS、TLS 和长连接。不需要把家庭端口映射到公网，语音 HTTP 服务用于可信局域网。

Windows 管理员 PowerShell 可按自己的真实地址建立最小入站规则（下面仍为示例，不自动执行）：

```powershell
New-NetFirewallRule -DisplayName 'Muse board TLS relay' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress 192.168.50.10 -LocalPort 443 -RemoteAddress 192.168.50.20
New-NetFirewallRule -DisplayName 'Muse board voice' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress 192.168.50.10 -LocalPort 8765 -RemoteAddress 192.168.50.20
```

只用女声就只需要 8765 入站规则。Linux 等系统按相同地址/端口配置；低于 1024 的 443 端口可能需要绑定权限。安装脚本不修改防火墙。

## 烧录与配网

按 [硬件与烧录指南](WAVESHARE_S3_185.zh-CN.md)用目标板覆盖配置和 `sdkconfig.local` 构建。必须用本仓库源码，不能下载上游其他板型的固件代替。

修改本地覆盖配置后，**已有生成 sdkconfig 不会自动重读所有默认值**。用相同构建目录的 `menuconfig` 修改并保存，或换新构建目录重新构建。仅修改 JSON 无法改变烧录到板子的 relay/TTS 地址；只改 JSON 中的允许来源不需要重新烧录。

Muse 手机端：`Settings > Devices > Developer mode` 开启后，从 `Settings > Devices > Add Device`（+）添加 `MuseGadget-…`。屏幕提示 `Confirm pairing` 时短按 BOOT；按手机流程选择 2.4 GHz Wi-Fi 并输入密码，等待设备显示连接成功。此板以屏幕状态为准，不照搬上游 RGB 灯颜色说明。

## 按层验收，不只看 Wi-Fi 图标

1. **构建/启动**：应用大小校验通过，正确板型启动，无 panic/反复重启。
2. **Wi-Fi**：路由器看得到板子并分配地址；这一步尚不表示 Muse 可达。
3. **电脑服务（C/女声）**：端口在监听。在 Windows 可用 `Test-NetConnection 192.168.50.10 -Port 443` 和 `-Port 8765`；只在电脑自己测试成功不证明板子到电脑畅通。
4. **语音 HTTP**：在示例电脑上 `curl.exe --noproxy "*" http://192.168.50.10:8765/health`，应返回 200 和音色。403 表示来源不在列表，连接拒绝/超时检查监听、地址和防火墙。`ready` 只代表本机 HTTP 服务，不保证微软在线合成成功。
5. **Muse TLS（C）**：relay 出现开发板到 Muse 的 `Connected`，表示代理 CONNECT 建立；还需板子屏幕/日志确认 Muse 会话上线。这不是最终语音对话验收。
6. **实际回复**：按住 BOOT 说“请回答：联网测试成功”，松开，确认屏幕出现有效回复。
7. **实际朗读**：回复完整读出，无内部编号；HTTP voice 日志有音频字节数。串口 `t` 固定朗读可单测语音链路，但不能代替步骤 6 的识别/模型验收。

可以在电脑测试原始 TLS 转发（电脑自身需在允许列表），保留服务器名和证书校验：

```powershell
curl.exe --noproxy "*" --connect-to api.muse.ai:443:192.168.50.10:443 https://api.muse.ai/ -I --max-time 15
```

收到 HTTP 状态（即使 401/404）仅证明这一主机的 TLS/HTTP 链路可达，不证明账号授权、所有 VM 主机或模型请求成功。不要使用跳过证书校验选项来掩盖 TLS 故障。

## 常见故障定位

| 表现 | 优先检查 |
|---|---|
| 手机找不到板子 | Developer mode、BLE 权限、板子是否已配对、屏幕状态 |
| 输入 Wi-Fi 密码后转圈 | 2.4 GHz、密码、DHCP；再检查 Muse 网络路径，不能只反复重输密码 |
| 昨天能用，今天没回复 | 电脑是否重启/休眠；relay/voice 是否还运行；代理端口和电脑 LAN 地址是否变化 |
| Wi-Fi 已连接，但无回复 | SDK token/配对，板子是否使用了电脑 relay 而服务没启动；代理到 Muse 的连通性 |
| 有字幕，无声音 | TTS URL、voice 服务、同意配置、speaker 设置、8765 防火墙、微软在线连通性 |
| voice 返回 403 | 允许列表没包含板子实际 IP，或 DHCP 地址变化 |
| voice 返回 503 | 在线合成失败/重试超时/并发繁忙；检查代理和微软网络路径 |
| 改了服务 IP，板子还找旧 IP | 配置只改在文件中；生成 sdkconfig 仍旧，或未重建/烧录固件 |
| IP 在同一网段但连接超时 | 访客 Wi-Fi、AP 隔离、主机防火墙、VPN 路由、服务只监听回环 |

## 本次检查结果（2026-10-09）

- 公开版独立编译已通过；主机语音与网络检查共 14 项通过，另外 47 项协议源码检查通过，分句/管线检查通过。
- 新增本机真实 TCP 测试使用 TLS ClientHello 和模拟 HTTP CONNECT 代理，验证字节双向转发、来源限制、域名边界；未联系云端，也不替代家庭网络实机验收。
- 用户实机首次测试“没有回复”。检查发现电脑 relay/voice 均停止、代理仍在运行。恢复原有服务后，日志确认开发板重新建立到 Muse API 和 hatch 的转发连接。
- 用户后续补充确认刚才已经可以正常回复，因此恢复后的原配置对话由用户确认为可用。新增手机回复同步与原始音频播放另行验证，不混同这次确认。
- 未重新烧录/抹除板子，未修改路由器或系统自启动。没有把本机私有配置或原始日志发布。
