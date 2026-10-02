# 日本出口 Docker 代理

使用 [wnlen/clash-for-linux](https://github.com/wnlen/clash-for-linux) 默认使用的 Mihomo 内核和其内置 Zashboard 面板。镜像固定 Mihomo `v1.19.23` 与上游提交 `42c26d8ad44373980ef3e6c4113de3beedb3d876`，直接以前台进程运行内核，不运行宿主机安装脚本或 systemd。

需要 Docker Engine、Docker Compose，以及**包含日本节点的 Clash / Mihomo YAML 订阅**。这个镜像不提供 VPN 账号或日本服务器。默认提供 HTTP / SOCKS5 应用代理；不自动接管整台机器的流量。

## 启动

在仓库根目录执行：

```bash
cd docker/japan-vpn
cp .env.example .env
chmod 600 .env
openssl rand -hex 24
```

编辑 `.env`，填入真实的 `CLASH_SUBSCRIPTION_URL`，将生成的随机值填入 `CLASH_CONTROLLER_SECRET`。不要将真实订阅或密钥写入 Dockerfile 或提交到 Git。

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=50 japan-vpn
```

默认端口：

| 用途 | 地址 |
| --- | --- |
| HTTP / SOCKS5 代理 | `127.0.0.1:7890` |
| 控制面板 | `http://127.0.0.1:9090/ui/` |
| 控制 API | `http://127.0.0.1:9090` |

面板连接 API 地址 `http://127.0.0.1:9090`，Secret 使用 `.env` 中的值。`JAPAN` 组默认选择 `JAPAN-AUTO` 自动测速，也可在面板手动选择日本节点。

## 使用与验证

```bash
# 请求出口 IP 和地理信息；实际返回的 country 应为 JP。
curl --fail --proxy http://127.0.0.1:7890 https://ipinfo.io/json

# SOCKS5：由代理端解析目标域名。
curl --fail --proxy socks5h://127.0.0.1:7890 https://ipinfo.io/json

# 让当前终端的常规 HTTP 客户端使用代理。
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export all_proxy=socks5h://127.0.0.1:7890
```

`JAPAN_FILTER` 按节点名称筛选，不验证地理位置；供应商可能给节点起错名字，最终应以代理请求查到的出口为准。面板里的浏览器出口信息可能来自浏览器自身，不能替代上面的代理请求检查。

只导入订阅的日本独立节点，忽略订阅的规则、控制器设置和其他节点。所有经代理端口进入的请求匹配 `MATCH,JAPAN`；日本节点不可用时不设置直连备用。没有匹配节点、订阅格式错误或依赖其他组时启动失败。支持含 `proxies` 列表的 YAML，不支持 Base64 链接列表或只有 `proxy-providers` 的配置；应向供应商索取 Clash / Mihomo 格式订阅。

订阅在每次启动时通过 HTTPS 拉取，最多 10 MiB，30 秒超时。更新节点或修改 `.env` 后执行：

```bash
docker compose up -d --force-recreate
```

生成的运行配置（含节点凭据）位于 Docker `state` 卷 `/data/config.yaml`，仅容器用户可读。镜像中不包含订阅或密钥。健康检查验证本地代理端口是否监听，出口可用性需要上述 `curl` 检查。

## 其他容器和远程使用

同一 Compose 网络的应用可使用 `http://japan-vpn:7890` 或 `socks5h://japan-vpn:7890`。同一网络内的容器能够访问此无认证代理，应只接入可信应用。

远程服务器默认只监听服务器的回环地址；从本机使用 SSH 转发：

```bash
ssh -N -L 7890:127.0.0.1:7890 -L 9090:127.0.0.1:9090 user@server
```

## 停止

```bash
docker compose down
# 删除含节点凭据的持久化配置时执行：
docker compose down -v
```

配置字段参见 [Mihomo 官方文档](https://wiki.metacubex.one/config/)。全机透明代理需要另外配置 TUN、路由和 DNS，此默认配置没有启用。
