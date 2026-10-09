# JAV百科事典

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

このリポジトリでは Zensical を使用して、中国語・日本語・英語の3言語の百科事典を構築しています。各言語のコンテンツは `docs/zh/`、`docs/ja/`、`docs/en/` に配置し、相対パスを統一しています。

## ディレクトリ構成と保守

公開コンテンツは人物、作品、産業、資料、特集に分類し、3言語で同じパスを使用しています。女優の五十音順の記事は `docs/{lang}/人物/女优/{行}/{段}/` に配置し、制作会社とレーベルは `产业/制作公司/` と `产业/厂牌/` に分けています。

保守資料、翻訳規約、名簿、名前の対応表は [maintenance/](maintenance/README.md) にまとめ、サイトには公開しません。スクリプトは用途別に `scripts/checks/`、`scripts/content/`、`scripts/i18n/`、`scripts/legacy/` に分類しています。詳しくは[スクリプトの説明](scripts/README.md)を参照してください。

ページの追加・移動、または分類メタデータの変更後は、索引とナビゲーション全体を再生成します。

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py
```

## ローカルプレビュー

日本の出口IPを持つプロキシが必要なローカルツールやスクレイピング処理には、[Docker の日本向けプロキシ設定](docker/japan-vpn/README.md)を利用できます。日本ノードのサブスクリプションは各自で用意してください。

FANZA 月間ランキングのプロキシ経由での取得、検証、公開手順と実行記録は、[日本向けプロキシによる取得ガイド](scrapers/fanza/JAPAN_PROXY.md)を参照してください。

ローカル保守環境では Python 3.12.14 と uv 0.12.5 を使用します。初回はロックファイルに従って依存関係をインストールします。

```bash
uv sync --locked --no-dev
uv run --locked --no-dev zensical build --config-file zensical.ja.toml --clean
uv run --locked --no-dev zensical build --config-file zensical.toml --clean
uv run --locked --no-dev zensical build --config-file zensical.en.toml --clean
```

ビルド結果は `site/` に出力されます。ローカルプレビューを起動するには、次のコマンドを実行します。

```bash
uv run --locked --no-dev zensical serve --config-file zensical.ja.toml
```

中国語と英語のプレビューには、それぞれ `zensical.toml` と `zensical.en.toml` を使用します。日本語版は `/`（既定の言語）、中国語版は `/zh/`、英語版は `/en/` に公開され、ヘッダーの言語選択で切り替えられます。3つの設定では `navigation.prune` を有効にし、各ページにサイト全体のナビゲーションが埋め込まれるのを防いでいます。`overrides/` は各ページに対応する別言語版へのリンクを生成します。

中国語（`docs/zh/`）が原文で、日本語と英語のディレクトリにはその翻訳を配置します。3言語の相対パスとファイル名は完全に一致させます。

翻訳方法、構造上の要件、品質面の制約、今後の保守規約については、[翻訳と保守のガイド](maintenance/TRANSLATION.md)を参照してください。

## 自動公開

CI は [Zensical 公式の GitHub Pages 手順](https://zensical.org/docs/publish-your-site/)を採用し、[.github/workflows/zensical.yml](.github/workflows/zensical.yml) に定義している。Pages の設定、リポジトリの取得、Python と依存関係のインストール、3言語の順次ビルド、`site/` 全体のアップロード、デプロイを行う。`master` または `main` への push で公開する。リポジトリの Pages の公開元は **GitHub Actions** に設定する。

最初に日本語を `site/` にビルドし、その後、中国語を `site/zh/`、英語を `site/en/` にビルドする。CI は保守スクリプトを呼び出さず、索引確認、3言語の検証、HTML リンク検証、pytest、Ruff、依存関係の監査を実行しない。`--strict` とビルドキャッシュも使用しない。これらの確認は保守担当者が手動で行う。CI は `ubuntu-latest`、Python `3.x`、Actions のメジャーバージョンタグを使用し、`pip install zensical` を直接実行する。`uv.lock`、厳密なバージョン固定、手動トリガー、追加のブランチ判定は使用しない。公式例との違いは、単一のビルドを3言語のビルドに展開した点のみである。

## Push 前の検証

`git push` の前に変更を完了させる。ページの追加・移動や分類メタデータの変更がある場合は、先に索引とナビゲーションを生成し、リポジトリのルートで次の検証を順に実行する。すべて成功した後に作業ツリーを確認し、今回の変更ファイルだけをステージしてコミットし、push する。失敗した検証は修正後に再実行する。検証後に変更を加えた場合は、影響する検証を再実行する。push 後の CI はビルドと公開のみを行うため、push 前の検証の代わりにはならない。

`./scripts/build_site.sh` は手動での一括検証用である。索引とナビゲーションの更新状況、3言語の内容を確認し、3言語を strict モードでビルドしてから、生成ページのリンク、アンカー、言語切り替え、サイズの上限を検証する。デプロイは行わず、CI からも呼び出さない。

```bash
./scripts/build_site.sh
uv run --locked --group dev --group scraper pytest
uv run --locked --group dev ruff format --check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev ruff check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev --group scraper pip-audit
git diff --check
```

次の個別検証は問題の切り分けに使用する。`check_site.py` の実行前には3言語をビルドする。

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py --check
uv run --locked --no-dev python scripts/checks/check_i18n.py
uv run --locked --no-dev python scripts/checks/check_site.py
```

`check_i18n.py` は3言語のファイルが一対一で対応していることを確認し、日本語・英語の各ページと中国語の原文について、front matter、見出し階層、リンク先、表の構造、コードブロックを比較します。相対リンクの解決、五十音の段別索引の網羅性、出演者リストと実際のページの対応、ランキングのスキーマと3言語の複製、作品ページの保護領域の完全一致も検証します。`./scripts/build_site.sh` は最初にこの検証を実行し、3言語のビルド完了後に `check_site.py` で生成ページの内部リンクとアンカーを検証する。いずれも手動で実行する。

`check_i18n.py` が検証するのは構造であり、意味の一致は対象外です。本文の行対応、数値・日付の比較、固有名詞の統一、未翻訳語句の確認など、言語間の内容校正は現在手作業で行っています。方法と翻訳校正の結果は、[翻訳と保守のガイド](maintenance/TRANSLATION.md)の「跨语言校对」節に記録しています。英語本文の表示名は `python3 scripts/i18n/en_fix_name_openings.py` で一括調整できます。この処理は何度実行しても同じ結果になり、`--check` を付けると変更を適用せずに報告します。

ローカル保守用の Python、Zensical、検証ツール、スクレイパーの依存関係は `pyproject.toml` にまとめ、具体的なバージョンは `uv.lock` で固定しています。自動公開では公式の pip によるインストールを採用し、このロックファイルは読み込みません。
