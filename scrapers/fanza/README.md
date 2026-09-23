# FANZA Actress Monthly Ranking Spider

通过 Playwright 抓取 FANZA 女优月度排名，并将结果写入三语内容树。

## 工作方式

1. 打开 `https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress`。
2. 精确等待 `ActressRankingPage` GraphQL POST 响应（`monthly + AV`、`limit=100`、`offset=0`）。
3. 严格验证响应 schema、连续排名、演员 ID 唯一性和必填字段。
4. 使用 UTC 时间生成文件名与 `fetched_at`。
5. 先写同目录临时文件，再原子替换目标；默认输出会逐字节镜像到中文、日文和英文目录。

脚本不会把页面错误、缺失字段或不足 `--limit` 条的数据当作成功结果。

## 安装

推荐从仓库根目录使用锁文件：

```bash
uv sync --locked --group scraper
uv run --locked --group scraper playwright install chromium
```

如需使用 pip：

```bash
python -m pip install -r scrapers/fanza/requirements.txt
python -m playwright install chromium
```

`scrapers/fanza/requirements.txt` 仅用于 pip 兼容；`pyproject.toml` 与 `uv.lock` 是项目的规范依赖源。

## 使用

所有命令从仓库根目录运行：

```bash
# 获取 Top 100，并自动镜像到三语目录
uv run --locked --group scraper python scrapers/fanza/spider.py

# 获取 Top 50
uv run --locked --group scraper python scrapers/fanza/spider.py --limit 50

# 显式使用代理；默认直连
uv run --locked --group scraper python scrapers/fanza/spider.py \
  --proxy socks5://127.0.0.1:7890

# 自定义输出目录；自定义目录不会改动三语仓库
uv run --locked --group scraper python scrapers/fanza/spider.py \
  --output ./output
```

`--limit` 必须是 1–100 的整数。默认输出为 `docs/zh/排名/actress-ranking-YYYYMM.yaml`，并自动写入内容完全相同的：

- `docs/ja/排名/actress-ranking-YYYYMM.yaml`
- `docs/en/排名/actress-ranking-YYYYMM.yaml`

任一目标写入失败时命令返回非零；随后仍应运行内容校验：

```bash
uv run --locked --no-dev python scripts/check_i18n.py
```

## 输出格式

```yaml
source: FANZA
type: actress_monthly_ranking
url: https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress
fetched_at: '2026-07-04T22:41:33.307301Z'
count: 100
rankings:
  - rank: 1
    actress_id: '1092427'
    name: 北岡果林
    image: https://awsimgsrc.dmm.co.jp/pics_dig/mono/actjpgs/kitaoka_karin.jpg
    contents_count: 367
    latest_content_id: ofje00710
    latest_title: 放心アクメしても子宮をグイグイ突きまくる！
```

排名文件中的键和值属于机器可读数据，三语保持逐字节一致，不进行翻译。
