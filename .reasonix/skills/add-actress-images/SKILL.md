---
name: add-actress-images
description: 为 javwiki 女优条目查找、核验、添加或修复头像图片。用于维护 thumbnail 和正文 actress-photo，排查失效、错人、低质量或许可不明的图片，以及安全使用仓库中的图片辅助脚本。
---

# 添加女优图片

在仓库根目录操作。图片必须同时满足“人物身份可确认、来源可追溯、允许站点使用、URL 可稳定访问”；找不到合格图片时保持空缺。

## 选择来源

按以下顺序查找：

1. Wikimedia Commons 文件页：确认人物、作者、许可和原始文件。
2. 本人事务所或厂商的官方资料页：确认其使用条款允许外链或转载。
3. 本人官方社交账号：仅在可确认授权且链接稳定时使用。

`namu.wiki`、搜索结果缩略图、聚合站和转载站只能作为线索，不能直接证明版权或人物身份。不要把“公开可见”等同于“可转载”。避免头像、海报、作品封面、水印图、截屏以及无法确认人物的合照。

## 核验

1. 用条目的日文名、别名和读音交叉确认人物，防止同名错配。
2. 打开图片来源页，而非只检查 CDN URL。
3. 检查图片链接返回成功、内容类型为图片且分辨率足够。
4. 对 Wikimedia 图片优先使用 `Special:Redirect/file/{文件名}` 或规范化缩略图 URL；记录对应文件页作为参考资料。
5. 检查仓库中是否已有同一人物的不同 URL，避免无意义替换。

活动照本身不是淘汰理由；应根据构图、清晰度、时效和身份可辨识度选择。不得仅凭文件名自动判断图片正确。

## 写入条目

在既有 YAML frontmatter 中加入：

```yaml
thumbnail: https://example.com/image.jpg
```

在 H1 后加入：

```html
<img src="https://example.com/image.jpg" alt="女优名" class="actress-photo" style="float: right; max-width: 280px; margin-left: 20px; border-radius: 8px;" />
```

保持 `thumbnail`、`src` 和条目人物完全一致。保留已有 `tags` 和其他 frontmatter；不要创建第二个 YAML 块。若更换图片，同时更新两个 URL，并在“参考资料”加入可审计的来源页（优先文件描述页，而非图片二进制地址）。

## 使用仓库脚本

先阅读脚本再运行。`scripts/add_image_display.py` 可为已有 `thumbnail` 补正文标签；其他抓图脚本可能批量写入文件、依赖缓存，且不能替代人工身份与许可核验。

运行批量脚本前：

```bash
git status --short
sed -n '1,220p' scripts/add_image_display.py
```

当前 `add_image_display.py` 没有参数解析，传入 `--help` 仍会直接修改全库。若脚本不支持预览或限定目标，不要直接执行。运行后逐项审查：

```bash
git diff --check
git diff -- src/
```

最后按 `../javwiki/SKILL.md` 的验证流程检查构建。不要因缺图而填入未经核验的候选 URL。
