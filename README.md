# JAV 百科 / JAV百科事典 / JAV Encyclopedia

本仓库使用 Zensical 构建中文、日文和英文三语百科。对应内容位于 `docs/zh/`、`docs/ja/` 和 `docs/en/`，并使用相同的相对路径。

This repository uses Zensical to build Chinese, Japanese, and English editions with matching paths under `docs/zh/`, `docs/ja/`, and `docs/en/`.

## 本地预览

项目使用 Zensical 构建文档站点：

```bash
./scripts/build_site.sh
```

构建结果位于 `site/`。启动本地预览：

```bash
uvx --from zensical==0.0.62 zensical serve --config-file zensical.toml
```

日文和英文可分别使用 `zensical.ja.toml`、`zensical.en.toml` 预览。中文版继续发布在 `/`，日文版发布在 `/ja/`，英文版发布在 `/en/`，页眉语言选择器可在三个版本间切换。

翻译方法、质量限制和后续维护约定见 [TRANSLATION.md](TRANSLATION.md)。提交内容变更前请运行 `python3 scripts/check_i18n.py`，确认三个语言目录中的文件一一对应。
