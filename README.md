# JAV 百科

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

本仓库使用 Zensical 构建中文、日文和英文三语百科。对应内容位于 `docs/zh/`、`docs/ja/` 和 `docs/en/`，并使用相同的相对路径。

## 目录与维护

公开内容按人物、作品、产业、资料和专题组织，三语保留相同路径。女优五十音条目位于 `docs/{lang}/人物/女优/{行}/{段}/`；制作公司与厂牌分开存放在 `产业/制作公司/`、`产业/厂牌/`。

维护资料、翻译约定、名单和姓名映射统一在 [maintenance/](maintenance/README.md)，不发布到站点。脚本按用途分为 `scripts/checks/`、`scripts/content/`、`scripts/i18n/` 和 `scripts/legacy/`，说明见 [脚本文档](scripts/README.md)。

新增、移动页面或修改分类元数据后，先生成索引和完整导航：

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py
```

## 本地预览

需要日本出口代理的本地工具或抓取任务，可使用 [Docker 日本代理配置](docker/japan-vpn/README.md)，并提供自己的日本节点订阅。

FANZA 月榜的代理抓取、校验与发布步骤及执行记录见 [日本代理抓取文档](scrapers/fanza/JAPAN_PROXY.md)。

本地维护环境使用 Python 3.12.14 与 uv 0.12.5。首次使用先安装锁文件中的依赖：

```bash
uv sync --locked --no-dev
uv run --locked --no-dev zensical build --config-file zensical.ja.toml --clean
uv run --locked --no-dev zensical build --config-file zensical.toml --clean
uv run --locked --no-dev zensical build --config-file zensical.en.toml --clean
```

构建结果位于 `site/`。启动本地预览：

```bash
uv run --locked --no-dev zensical serve --config-file zensical.ja.toml
```

中文和英文可分别使用 `zensical.toml`、`zensical.en.toml` 预览。日文版发布在 `/`（默认语言），中文版发布在 `/zh/`，英文版发布在 `/en/`，页眉语言选择器可在三个版本间切换。三份配置启用 `navigation.prune` 以避免每个页面嵌入完整站点导航；`overrides/` 负责生成逐页语言对应链接。

中文（`docs/zh/`）是源内容，日文与英文目录是它的翻译，三者相对路径、文件名完全一致。

翻译方法、结构契约、质量限制和后续维护约定见 [翻译与维护约定](maintenance/TRANSLATION.md)。

## 自动发布

CI 采用 [Zensical 官方 GitHub Pages 流程](https://zensical.org/docs/publish-your-site/)，配置位于 [.github/workflows/zensical.yml](.github/workflows/zensical.yml)：设置 Pages、检出仓库、安装 Python 和依赖、依次构建三语、上传整个 `site/`，最后部署。推送到 `master` 或 `main` 时触发发布；仓库 Pages 的发布来源需设为 **GitHub Actions**。

日文先构建到 `site/`，再将中文和英文构建到 `site/zh/`、`site/en/`。CI 不调用维护脚本，不执行索引检查、三语校验、HTML 链接检查、pytest、Ruff 或依赖审计，也不启用 `--strict` 或构建缓存。这些检查由维护者手动执行。CI 使用 `ubuntu-latest`、Python `3.x` 和 Actions 主版本标签，直接执行 `pip install zensical`；不使用 `uv.lock`、精确版本、手动触发或额外分支判断。相较官方示例，仅将单次构建展开为三语构建。

## 手动校验与测试

`./scripts/build_site.sh` 是手动完整校验入口：检查索引和导航是否已更新、校验三语内容、严格构建三个版本，再检查生成页面的链接、锚点、语言切换和体积预算。它不负责部署，也不由 CI 调用。

```bash
./scripts/build_site.sh
```

也可按需分别运行检查、测试、格式检查和依赖审计。`check_site.py` 需要先完成三语构建：

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py --check
uv run --locked --no-dev python scripts/checks/check_i18n.py
uv run --locked --no-dev python scripts/checks/check_site.py
uv run --locked --group dev --group scraper pytest
uv run --locked --group dev ruff format --check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev ruff check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev --group scraper pip-audit
```

`check_i18n.py` 检查三个语言目录的文件一一对应，并逐页比对日文、英文与中文源的 front matter、标题层级、链接目标、表格形状和代码块；此外校验相对链接可解析、段索引覆盖完整、演员列表与真实页面映射、排名 schema 与三语镜像、作品页受保护区逐字一致。`./scripts/build_site.sh` 会先执行这项检查，三语构建完成后再由 `check_site.py` 校验生成页面的内部链接和锚点；两项检查均为手动执行。

`check_i18n.py` 只覆盖结构，不覆盖语义。跨语言内容校对（正文行对齐、数字与日期比对、专名一致性、未翻译残词）目前是人工流程，方法与本轮结果记录在 [翻译与维护约定](maintenance/TRANSLATION.md) 的「跨语言校对」小节。英文正文显示名的批量对齐由 `python3 scripts/i18n/en_fix_name_openings.py`（加 `--check` 只报告）保证幂等。

本地维护所用的 Python、Zensical、校验工具和抓取器依赖记录在 `pyproject.toml`，具体版本由 `uv.lock` 固定。自动发布采用官方的 pip 安装方式，不读取这个锁文件。
