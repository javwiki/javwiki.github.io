# JAV 百科 / JAV百科事典 / JAV Encyclopedia

本仓库使用 Zensical 构建中文、日文和英文三语百科。对应内容位于 `docs/zh/`、`docs/ja/` 和 `docs/en/`，并使用相同的相对路径。

This repository uses Zensical to build Chinese, Japanese, and English editions with matching paths under `docs/zh/`, `docs/ja/`, and `docs/en/`.

## 本地预览

项目使用 Python 3.12.14 与 uv 0.12.5。首次使用先安装锁文件中的依赖：

```bash
uv sync --locked --no-dev
./scripts/build_site.sh
```

构建结果位于 `site/`。启动本地预览：

```bash
uv run --locked --no-dev zensical serve --config-file zensical.toml
```

日文和英文可分别使用 `zensical.ja.toml`、`zensical.en.toml` 预览。中文版继续发布在 `/`，日文版发布在 `/ja/`，英文版发布在 `/en/`，页眉语言选择器可在三个版本间切换。三份配置启用 `navigation.prune` 以避免每个页面嵌入完整站点导航；`overrides/` 负责生成逐页语言对应链接。

中文（`docs/zh/`）是源内容，日文与英文目录是它的翻译，三者相对路径、文件名完全一致。

翻译方法、结构契约、质量限制和后续维护约定见 [TRANSLATION.md](TRANSLATION.md)。

## 校验与测试

```bash
uv run --locked --no-dev python scripts/check_i18n.py
uv run --locked --group dev --group scraper pytest
uv run --locked --group dev ruff format --check scripts/check_i18n.py scripts/check_site.py scrapers/fanza/spider.py tests
uv run --locked --group dev ruff check scripts/check_i18n.py scripts/check_site.py scrapers/fanza/spider.py tests
uv run --locked --group dev --group scraper pip-audit
```

`check_i18n.py` 检查三个语言目录的文件一一对应，并逐页比对日文、英文与中文源的 front matter、标题层级、链接目标、表格形状和代码块；此外校验相对链接可解析、段索引覆盖完整、演员列表与真实页面映射、排名 schema 与三语镜像、作品页受保护区逐字一致。`./scripts/build_site.sh` 与 CI 都会先执行这项检查，三语构建完成后再由 `check_site.py` 校验生成页面的内部链接和锚点。

Python、Zensical、校验工具和抓取器依赖统一记录在 `pyproject.toml`，具体版本由 `uv.lock` 固定；CI 使用 `--locked`，不会在构建时静默更新依赖。
