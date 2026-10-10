---
title: 排名
---

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
| [actress-ranking-202610.yaml](actress-ranking-202610.yaml) | 女优月间排名 | FANZA | 2026年10月 | 100 |

## FANZA 历史排名查询来源

以下网站于2026年10月10日核查，用于查找历史榜单或补充排名线索。它们是第三方资料，保存范围和统计口径各不相同；本节为来源目录，相关数据尚未导入本站的 YAML 文件。

| 网站与示例 | 榜单类型 | 保存范围与使用限制 |
| --- | --- | --- |
| [Proclivity-DB 月榜目录](https://proclivity-db.com/ranking/fanza/video)；[2026年4月示例与记录规则](https://proclivity-db.com/ranking/fanza/video/y2026/2026-04) | FANZA 视频区女优月榜 TOP100 | 自2025年12月开始记录，包含前月变化、记录期间最高名次及部分官方截图。该站将每月1日抓取的榜单归为上月，月份归属是其记录规则，可能与官方更新时点不同；“最高名次”仅覆盖其记录期间。 |
| Adultinfojpn：[2022年度榜](https://adultinfojpn.com/avstar_ranking/fanza2022/)；[2023年度榜](https://adultinfojpn.com/avstar_ranking/fanza2023/) | FANZA DVD 销售女优年度 TOP100 | 已核查两个年份的完整名单，属于第三方转载；未确认其他年份是否连续保存。 |
| [moe zine：2024年1月榜](https://www.moezine.com/1032716/) | FANZA DVD 通贩女优月榜 | 页面收录月榜视频及文字名次，标明排名来源为 FANZA 通販DVD；适合查找旧月榜，未确认月份是否连续。 |
| [BKR B：女优排名记录示例](https://av.bkrb.net/actress/1085279/ranking/) | 根据 FANZA 销售榜自行计算的女优人气排名 | 可查单个女优的排名走势、首次入榜与最高名次；属于站方自行计算，不能作为 FANZA 官方女优榜的原始名次。 |

[AV知りたい的排名存档目录](https://av-shiritai.com/works/ranking/archive)也提供历史月份入口，但抽查的[2024年12月页面](https://av-shiritai.com/works/ranking/archive/2024-12)保存的是 MGS 与 Pcolle 榜单。因此，不能仅凭存档入口将该站列为已确认的 FANZA 历史榜来源。

## 历史排名的记录口径

- 分别标注视频区、DVD 通贩区、租赁区，区分作品榜与女优榜，以及日榜、周榜、月榜、年度榜；不同口径不直接合并比较。
- 保留来源 URL、榜单所述期间和抓取时间。第三方页面的发布日或快照采集日不自动等于官方统计期间；月份归属规则应单独说明。
- 区分官方原榜、第三方转载、第三方重新计算的排名。转载核查和推算结果须注明来源性质；本站某月抓取的榜单也不自动代表该月结束后的最终排名。
