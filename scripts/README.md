# 维护脚本

所有命令从仓库根目录运行。

```text
scripts/
├── build_site.sh         # 手动三语严格构建与校验入口
├── checks/               # 源内容和生成站点的校验
├── content/              # 分类索引与导航生成
├── i18n/                 # 翻译装配、显示名和五十音索引维护
└── legacy/               # 归档的一次性抓取与修复脚本
```

| 路径 | 用途 |
| --- | --- |
| `build_site.sh` | 检查生成索引与导航、三语内容与维护数据，再严格构建三个版本，最后校验站内链接、语言切换和页面体积。 |
| `checks/check_i18n.py` | 检查三语结构、相对链接、女优索引覆盖、维护列表、排名镜像、作品受保护区和制作公司关系元数据。 |
| `checks/check_site.py` | 检查生成 HTML 的内部文件链接、锚点、语言切换和体积预算。 |
| `content/generate_indexes.py` | 从制作公司／厂牌元数据生成分类索引，从目录和本语页面标题生成三个配置中的完整导航；`--check` 只检查漂移。 |
| `i18n/en_display_names.py` | 从中文源生成英文显示名，更新英文页面与 `maintenance/en/list.{md,yaml}`；`--check` 只报告。 |
| `i18n/en_index_pages.py` | 重建英文五十音行段索引和维护列表标题。 |
| `i18n/en_fix_name_openings.py` | 修正文首的英文显示名；`--check` 只报告。 |
| `i18n/assemble_actress.py` | 装配英文女优条目的 front matter 和图片，再检查结构；`--check` 只报告。 |

CI 按官方示例通过 `pip install zensical` 安装并直接执行三语普通构建、部署，不读取本地维护的 `uv.lock`，不调用本目录中的校验脚本。`build_site.sh` 保留为手动完整校验入口。

新增或移动页面、调整标题或关系元数据后，手动更新索引与导航，再执行校验：

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py
./scripts/build_site.sh
uv run --locked --group dev --group scraper pytest
uv run --locked --group dev ruff format --check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev ruff check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev --group scraper pip-audit
```

三语共用相对路径；女优页面位于 `docs/{lang}/人物/女优/{行}/{段}/`。维护资料和姓名映射见 [maintenance](../maintenance/README.md)，翻译约定见 [TRANSLATION.md](../maintenance/TRANSLATION.md)。

`legacy/` 中的脚本依赖已不存在的旧输入目录，保留作历史参考，不纳入日常构建。复用前需先调整输入、输出与依赖。
