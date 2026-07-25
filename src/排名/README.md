# 排名

本目录收录各类AV相关排名数据，如月间人气女优排名等。

## 数据文件

排名数据以 YAML 格式存储，每份文件包含以下字段：

- `source`: 数据来源（如 FANZA）
- `type`: 排名类型（如 `actress_monthly_ranking`）
- `url`: 源数据 URL
- `fetched_at`: 抓取时间
- `count`: 排名条目数量
- `rankings`: 排名列表，每项包含 `rank`、`name`、`actress_id`、`contents_count`、`latest_title` 等

## 排名列表

| 文件 | 类型 | 来源 | 日期 | 数量 |
| --- | --- | --- | --- | --- |
| [actress-ranking-202606.yaml](actress-ranking-202606.yaml) | 女优月间排名 | FANZA | 2026年6月 | 100 |
| [actress-ranking-202607.yaml](actress-ranking-202607.yaml) | 女优月间排名 | FANZA | 2026年7月 | 100 |
