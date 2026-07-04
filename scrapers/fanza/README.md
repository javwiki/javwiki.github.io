# FANZA Actress Monthly Ranking Spider

通过 Playwright 抓取 FANZA 女优月度销量排名

## 技术原理

1. 使用 Playwright 打开页面 `https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress`
2. 拦截页面加载时的 GraphQL API 响应 (`api.video.dmm.co.jp/graphql`)
3. 从响应中提取 `ppvActressRanking` 数据
4. 保存为 YAML 文件

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用

```bash
# 获取 Top 100
python spider.py

# 指定数量
python spider.py --limit 50

# 指定代理
python spider.py --proxy socks5://127.0.0.1:7890

# 指定输出目录
python spider.py --output ./output
```

## 输出格式

```yaml
source: FANZA
type: actress_monthly_ranking
url: https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress
fetched_at: '2026-06-26T02:30:00'
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
