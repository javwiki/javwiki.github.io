---
title: Rankings
---

# Rankings

This directory collects AV-related ranking data, such as monthly actress popularity rankings.

## Data files

Ranking data is stored as YAML. Each file contains the following fields:

- `source`: the data source (e.g. FANZA)
- `type`: the ranking type (e.g. `actress_monthly_ranking`)
- `url`: URL of the source data
- `fetched_at`: fetch timestamp
- `count`: number of ranking rows
- `rankings`: the ranking list; each item carries `rank`, `name`, `actress_id`, `contents_count`, `latest_title` and more

## Ranking list

| File | Type | Source | Fetch date | Rows |
| --- | --- | --- | --- | --- |
| [actress-ranking-202606.yaml](actress-ranking-202606.yaml) | Monthly actress ranking | FANZA | 2026-06-26 | 100 |
| [actress-ranking-202607.yaml](actress-ranking-202607.yaml) | Monthly actress ranking | FANZA | 2026-07-04 | 100 |
| [actress-ranking-202610.yaml](actress-ranking-202610.yaml) | Monthly actress ranking | FANZA | 2026-10-02 | 100 |

These files preserve snapshots returned by FANZA’s video-floor `term=monthly&type=actress` ranking at collection time. Filename months identify collection months, not final monthly rankings. Table dates come from each file’s `fetched_at`. The older June and July timestamps have no timezone; October’s `Z` means UTC. Do not infer missing timezones. There are only three snapshots, not a continuous monthly series; they cannot establish a complete annual ranking or changes in monthly sales.

## Sources for historical FANZA rankings

These sites were checked on 10 October 2026 as sources for historical rankings or related records. They are third-party resources with different coverage and methods. This section is a source directory; their data has not yet been imported into this site's YAML files.

| Site and example | Ranking type | Coverage and limitations |
| --- | --- | --- |
| [Proclivity-DB monthly archive](https://proclivity-db.com/ranking/fanza/video); [April 2026 example and recording rules](https://proclivity-db.com/ranking/fanza/video/y2026/2026-04) | FANZA video-floor monthly actress TOP100 | Records begin in December 2025, with monthly changes, highest recorded positions and some official screenshots. The site assigns snapshots taken on the first of each month to the previous month; this is its own recording rule and may differ from official update timing. Highest positions cover only its recording period. |
| Adultinfojpn: [2022 annual ranking](https://adultinfojpn.com/avstar_ranking/fanza2022/); [2023 annual ranking](https://adultinfojpn.com/avstar_ranking/fanza2023/) | FANZA annual actress TOP100 based on DVD sales | Complete lists were checked for both years. These are third-party reproductions; continuous coverage of other years has not been confirmed. |
| [moe zine: January 2024 ranking](https://www.moezine.com/1032716/) | FANZA DVD mail-order monthly actress ranking | Includes a ranking video and positions in text, identifying FANZA mail-order DVD as the source. Useful for locating older monthly lists; continuous monthly coverage has not been confirmed. |
| [BKR B: example of an actress ranking record](https://av.bkrb.net/actress/1085279/ranking/) | Actress popularity ranking independently calculated from FANZA bestseller rankings | Provides individual ranking trends, first appearances and highest positions. These are the site's own calculations and cannot be treated as original positions in FANZA's official actress ranking. |

[AV Shiritai's ranking archive directory](https://av-shiritai.com/works/ranking/archive) also links to historical months, but the checked [December 2024 page](https://av-shiritai.com/works/ranking/archive/2024-12) preserves MGS and Pcolle rankings. The archive directory alone does not establish that the site preserves historical FANZA rankings.

## Recording historical rankings

- Identify the video, DVD mail-order or rental floor, distinguish works from actresses, and label daily, weekly, monthly or annual rankings. Do not directly combine or compare rankings with different scopes.
- Preserve the source URL, stated ranking period and fetch timestamp. A third-party publication date or snapshot date does not automatically establish the official reporting period; explain any rule used to assign a month.
- Distinguish official original rankings, third-party reproductions and independently calculated rankings. Label the source type for reproduced or estimated results; a ranking fetched by this site during a month is not automatically that month's final ranking.
