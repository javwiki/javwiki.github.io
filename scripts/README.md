# scripts/

本站点的维护脚本。所有脚本从仓库根目录运行。

| 文件 | 用途 |
|---|---|
| `build_site.sh` | 构建入口。自动切换到仓库根目录，使用 `uv.lock` 固定环境，先跑 `check_i18n.py`，再以 Zensical 的 `--strict` 模式依次构建中文、日文、英文三个版本，最后运行 `check_site.py`。 |
| `check_i18n.py` | 内容结构与数据完整性校验。运行依赖由根目录 `pyproject.toml` 与 `uv.lock` 统一管理。检查项见 `TRANSLATION.md` 的「验证」一节。 |
| `check_site.py` | 构建后校验三语静态页面的内部文件链接、锚点、逐页语言链接及 HTML/导航体积预算。 |
| `ja_name_map.json` | 中文条目名 → 日文标准写法对照表，日文版重建与后续维护共用。 |
| `en_display_names.py` | 从中文源 `英文名` 字段生成英文显示名，应用到 `docs/en` 的 H1、`alt`、链接显示名与 `_meta/list.{md,yaml}`（幂等）。 |
| `en_index_pages.py` | 依据中文源重建 47 个五十音行/段索引页与 `docs/en/_meta/list.md` 标题。 |
| `assemble_actress.py` | 装配女优页：合并中文源 front matter 与 `<img>`（`alt` 本地化为英文名）并即时跑结构校验；不要与写文件同批执行（会竞争）。 |

```bash
./scripts/build_site.sh
uv run --locked --no-dev python scripts/check_i18n.py
uv run --locked --group dev --group scraper pytest
```

## legacy/

12 个一次性抓取/修复脚本，2026-09 内容审查后归档：

```
add_image_display.py          add_verified_external_images.py
add_verified_namu_images.py   add_wiki_images.py
add_wikidata_actor_images.py  audit_images.py
batch_fetch.py                better_fetch_images.py
fetch_wiki_images.py          reliable_fetch_images.py
remove_wiki_images.py         retry_wiki_images.py
```

它们依赖的输入路径（`docs/images/`、`wiki_fetch/` 等）已不存在，对当前仓库运行会静默无操作，因此不再与活跃脚本并列放置。如需复用其中逻辑，先把依赖补齐再移回 `scripts/` 根目录。

同期还删除了无引用的缓存产物：`scripts/icache.json`、`scripts/image_cache2.json`、`scripts/wiki_images_cache.json`、`scripts/test_arzon.html`。
