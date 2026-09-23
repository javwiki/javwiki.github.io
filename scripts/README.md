# scripts/

本站点的维护脚本。所有脚本从仓库根目录运行。

| 文件 | 用途 |
|---|---|
| `build_site.sh` | 构建入口。先跑 `check_i18n.py`，再以 `zensical==0.0.62` 的 `--strict` 模式依次构建中文、日文、英文三个版本。 |
| `check_i18n.py` | 内容结构与数据完整性校验（需 PyYAML，已由 `build_site.sh` 通过 `uvx --with pyyaml` 提供）。检查项见 `TRANSLATION.md` 的「验证」一节。 |
| `ja_name_map.json` | 中文条目名 → 日文标准写法对照表，日文版重建与后续维护共用。 |

```bash
./scripts/build_site.sh                # 校验 + 三语构建
uvx --with pyyaml python3 scripts/check_i18n.py   # 只跑校验
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
