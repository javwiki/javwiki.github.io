# 通过日本代理抓取 FANZA 月榜

本文记录日本代理的启动、出口验证、榜单抓取与发布流程，以及 2026-10-02 的实际执行结果。所有命令从仓库根目录运行。Docker 镜像的构建与端口配置见 [Docker 使用说明](../../docker/japan-vpn/README.md)，抓取器的参数和数据格式见 [抓取器说明](README.md)。

## 1. 准备订阅和本地密钥

```bash
cp docker/japan-vpn/.env.example docker/japan-vpn/.env
chmod 600 docker/japan-vpn/.env
openssl rand -hex 24
```

如果 `.env` 已经配置，直接使用现有文件，不要重新复制覆盖。将订阅 URL 和生成的随机密钥分别填入 `.env` 的 `CLASH_SUBSCRIPTION_URL` 与 `CLASH_CONTROLLER_SECRET`。该文件已被 Git 忽略，Docker 构建上下文也排除了它。

本次使用的供应商需要 `flag=meta` 才能返回包含真实 Hysteria2 / VLESS 节点的 Mihomo 配置。URL 格式如下，令牌由使用者自行填写：

```text
https://www.yfjc.xyz/api/v1/client/subscribe?token=<YOUR_TOKEN>&flag=meta
```

本次观察到：原始 URL 返回字符串格式订阅；`flag=clash` 返回客户端协议不兼容的提示节点；`flag=meta` 返回 54 个节点，其中 21 个匹配默认日本名称筛选。其他供应商的格式参数应按其说明设置。

不要把真实订阅 URL、节点凭据或控制密钥写入文档、镜像、Git 提交或公开日志。

## 2. 启动并验证日本出口

```bash
docker compose -f docker/japan-vpn/compose.yaml up -d --build
docker compose -f docker/japan-vpn/compose.yaml ps

# HTTP 代理出口验证：返回 country=JP。
curl --fail --show-error --max-time 30 \
  --proxy http://127.0.0.1:7890 https://api.country.is/

# SOCKS5 出口验证，并由代理端解析域名。
curl --fail --show-error --max-time 30 \
  --proxy socks5h://127.0.0.1:7890 https://api.country.is/

# 备用查询：返回 loc=JP。
curl --fail --show-error --max-time 30 \
  --proxy http://127.0.0.1:7890 https://www.cloudflare.com/cdn-cgi/trace
```

容器应显示 `healthy`。健康检查只验证代理端口监听，出口国家仍须通过代理请求确认。镜像按节点名称筛选日本节点，不能仅凭名称认定出口位于日本。

控制面板为 `http://127.0.0.1:9090/ui/`，API 地址为 `http://127.0.0.1:9090`；连接密钥取自本地 `.env`。`JAPAN` 默认选择 `JAPAN-AUTO`，也可手动选择其中的日本节点。所有进入代理端口的流量匹配 `MATCH,JAPAN`，没有配置直连备用。

如果当前用户无权访问 Docker socket，在 Docker 命令前加 `sudo`。端口仅绑定运行容器的机器的回环地址；远程使用方式见 Docker 使用说明。

## 3. 抓取 Top 100

```bash
uv sync --locked --group scraper
uv run --locked --group scraper playwright install chromium
uv run --locked --group scraper python scrapers/fanza/spider.py \
  --proxy http://127.0.0.1:7890
```

抓取器显式为 Chromium 设置代理，等待 FANZA 页面实际发出的 `ActressRankingPage` GraphQL 响应，验证月榜查询、连续排名、唯一演员 ID 与必填字段，再保存数据。不依赖终端的代理环境变量。

默认保存 `docs/zh/排名/actress-ranking-YYYYMM.yaml`，并逐字节同步至 `docs/ja/排名/` 和 `docs/en/排名/`。`YYYYMM` 来自 UTC 抓取时间；同月再次运行会覆盖该月快照。文件记录抓取时页面返回的月榜，不代表该自然月结束后的最终榜单。

## 4. 更新索引、校验与发布

新月份抓取完成后，在以下索引中加入对应 YAML 链接、本地化月份及条目数量：

- [中文榜单索引](../../docs/zh/排名/index.md)
- [日文榜单索引](../../docs/ja/排名/index.md)
- [英文榜单索引](../../docs/en/排名/index.md)

```bash
./scripts/build_site.sh
git diff --check
git status --short
```

构建脚本依次检查三语内容结构与数据、严格构建三个语言版本、校验站点链接。确认通过后，仅暂存本次生成的三份 YAML 和三个索引文件，按仓库要求提交并推送 `main`。

## 2026-10-02 执行记录

| 项目 | 实际结果 |
| --- | --- |
| 代理 | Mihomo `v1.19.23`，容器 `healthy` |
| 日本节点 | 21 个，默认策略 `JAPAN-AUTO` |
| 出口验证 | HTTP 与 SOCKS5 均成功；`203.10.99.59`，国家 `JP`；Cloudflare 接入点 `NRT` |
| 抓取时间 | `2026-10-02T06:28:13.283809Z` |
| 榜单 | FANZA 女优月榜 Top 100，排名连续，演员 ID 唯一 |
| 数据文件 | [actress-ranking-202610.yaml](../../docs/zh/排名/actress-ranking-202610.yaml) |
| 三语数据 | 中文、日文、英文 YAML 逐字节一致 |
| 校验 | 三语结构校验、三语严格构建、站点链接校验全部通过 |
| 发布提交 | `982a926`，已推送 `main` |

前三名为逢沢みゆ、河北彩花（河北彩伽）、松本いちか。出口 IP、节点数量和排名是本次执行的观测结果，后续运行可能变化。

## 已遇到的问题

| 现象 | 本次处理 |
| --- | --- |
| 提示 Chromium executable 不存在 | 执行 `uv run --locked --group scraper playwright install chromium` 后重试 |
| 订阅不是 YAML，或没有匹配的日本节点 | 对本次供应商使用 `flag=meta`；`flag=clash` 的提示节点不是可用节点 |
| 出口查询 `ipinfo.io` 返回 HTTP 429 | 改用 `api.country.is` 和 Cloudflare trace 确认日本出口 |
| Docker socket permission denied | 使用具备 Docker 权限的账户或 `sudo` 执行 Docker 命令 |

修改订阅或密钥后，应执行 `docker compose -f docker/japan-vpn/compose.yaml up -d --force-recreate`，让容器重新读取 `.env` 并拉取订阅。
