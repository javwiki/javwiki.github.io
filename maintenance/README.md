# 百科维护资料

本目录不参与站点发布。中文是源资料，`zh/`、`ja/`、`en/` 保留相同文件结构。

```text
maintenance/
├── README.md
├── TRANSLATION.md        # 翻译、三语结构契约与历史记录
├── todo.md               # 建设计划与执行记录
├── ja_name_map.json      # 中文文件名与日文艺名对照
├── zh/                  # 中文维护资料
├── ja/                  # 日文维护资料
└── en/                  # 英文维护资料
```

每个语言目录包含资料来源、五十音定位规则、女优文本列表和 YAML 列表。`scripts/checks/check_i18n.py` 会检查维护文档的三语结构、仓库链接、列表 schema、名单顺序以及对应的真实女优页面；移出公开站点不会取消数据校验。

## 当前内容目录

```text
docs/{lang}/
├── index.md
├── 人物/
│   ├── 女优/{行}/{段}/
│   ├── 男优/
│   ├── 导演/
│   └── 组合/
├── 作品/
│   ├── 单部/
│   ├── 系列/
│   └── 番号/
├── 产业/
│   ├── 制作公司/
│   ├── 厂牌/
│   ├── 经纪公司/
│   └── 协会/
├── 资料/
│   ├── 奖项/
│   ├── 活动/
│   ├── 排名/
│   ├── 法律/
│   └── 术语/
└── 专题/
```

## 制作公司与厂牌元数据

制作公司条目的 `entity_type` 为 `company` 或 `group`；厂牌为 `brand`。元数据键和值在三语间完全一致，页面标题与索引说明各自翻译。

```yaml
entity_type: brand
relationships:
- type: published_by
  target: ../制作公司/Prestige.md
  source: https://www.suruga-ya.jp/product/detail/131932638
```

`published_by` 表示发行关系；`production_lineage` 表示来源支持的制作系谱。两者都不能当作未经核实的持股关系。每项关系必须提供公司条目的相对路径及 HTTPS 来源。生成器据此维护制作公司、厂牌索引；读者入口位于 [产业与组织](../docs/zh/产业/index.md)。

## 新增与移动条目

1. 同步修改三语对应页面与正文链接。女优条目还需要更新行段索引及各语言的 `list.md`、`list.yaml`。
2. 执行 `uv run --locked --no-dev python scripts/content/generate_indexes.py`，更新分类索引和三份配置中的导航。
3. 在 push 前手动执行 `./scripts/build_site.sh`、pytest、Ruff、依赖审计和 `git diff --check`，完整命令见 [脚本文档](../scripts/README.md)。失败时先修复并重跑；校验后继续修改时，重跑受影响的检查。
4. 全部通过后检查工作区，只暂存本次修改的文件，提交并 push；这些检查不在 CI 中自动运行。

2026-10-09 已迁移到上述目录。按本轮要求不保留旧 URL，也不生成重定向。当前相对链接及语言切换仍须可用。

## 自动发布与手动校验

[发布 workflow](../.github/workflows/zensical.yml) 采用 [Zensical 官方 GitHub Pages 流程](https://zensical.org/docs/publish-your-site/)，在推送到 `master` 或 `main` 时依次构建日文、中文、英文，上传 `site/` 并部署。除三语构建外，workflow 与官方示例一致：使用 `ubuntu-latest`、Python `3.x`、Actions 主版本标签和 `pip install zensical`，不读取 `uv.lock`，不增加手动触发或分支判断。CI 只构建和发布，不自动检查索引、三语结构、生成页面链接，不运行 pytest、Ruff、pip-audit 或 `--strict`。`scripts/build_site.sh` 保留为手动完整校验入口；维护者须在每次 push 前完成上述校验，通过后再提交、推送。
