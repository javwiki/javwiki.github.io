# ランキング

本ディレクトリには、月間人気女優ランキングなど、AV関連の各種ランキングデータを収録しています。

## データファイル

ランキングデータは YAML 形式で保存され、各ファイルには次のフィールドが含まれます。

- `source`: データの出典（例：FANZA）
- `type`: ランキングの種類（例：`actress_monthly_ranking`）
- `url`: 元データの URL
- `fetched_at`: 取得日時
- `count`: ランキングの件数
- `rankings`: ランキングの一覧。各項目には `rank`、`name`、`actress_id`、`contents_count`、`latest_title` などが含まれる

## ランキング一覧

| ファイル | 種類 | 出典 | 日付 | 件数 |
| --- | --- | --- | --- | --- |
| [actress-ranking-202606.yaml](actress-ranking-202606.yaml) | 女優月間ランキング | FANZA | 2026年6月 | 100 |
| [actress-ranking-202607.yaml](actress-ranking-202607.yaml) | 女優月間ランキング | FANZA | 2026年7月 | 100 |
