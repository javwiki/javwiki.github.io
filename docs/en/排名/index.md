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

| File | Type | Source | Date | Rows |
| --- | --- | --- | --- | --- |
| [actress-ranking-202606.yaml](actress-ranking-202606.yaml) | Monthly actress ranking | FANZA | June 2026 | 100 |
| [actress-ranking-202607.yaml](actress-ranking-202607.yaml) | Monthly actress ranking | FANZA | July 2026 | 100 |
