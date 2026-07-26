---
name: add-actress-images
description: 从维基百科、namu.wiki、事务所官网、社交媒体获取女优图片并写入条目的步骤指南
---

# 女优图片获取与添加指南

为女优条目添加正确头像的标准化步骤。

## 优先来源（按可靠性排序）

### 1. 维基百科（Wikimedia Commons）

**中文维基百科** `https://zh.wikipedia.org/wiki/{女优名}`
- 页面右侧信息框的主图通常是可靠的专业肖像
- 右键图片 → "在新标签页中打开图片" → 复制 URL
- URL 格式示例：`https://upload.wikimedia.org/wikipedia/commons/.../xxx.jpg`

**日文维基百科** `https://ja.wikipedia.org/wiki/{女优名}`
- 日本 AV 女优在日文维基上通常有更完整的条目和图片
- 同样从信息框获取图片 URL

**Wikimedia Commons 分类页** `https://commons.wikimedia.org/wiki/Category:{女优名}`
- 浏览该女优的所有上传图片
- 优先选择文件名为 `{女优名}.jpg` 的图片（通常是专业肖像）
- 避免使用活动照（Trend Girls、Kindai Mahjong、TRE 等事件照片）
- 避免使用 PNG/SVG 格式（通常是 Logo 或截屏）

### 2. namu.wiki（韩文维基）

`https://namu.wiki/w/{女优名}`
- 韩文维基上 AV 女优条目通常有头像
- 从页面信息框获取图片 URL

### 3. 事务所官网

常见事务所官网（含女优资料页）：
- **T-POWERS**: `https://t-powers.co.jp/official/talent/{name}/`
- **Mine's**: `https://mines-pro.jp/actor/{name}/`
- **C-more**: `https://cmore.jp/actress/{name}/`
- **Bambi**: `https://bambi-promotion.com/actress/{name}/`
- **ACT**: `https://act-ice.com/actress/{name}/`
- **8MAN**: `https://8man.jp/actress/{name}/`
- **LIGHT**: `https://light-japan.com/actress/{name}/`
- **All Promotion**: `https://all-pro.co.jp/talent/{name}/`

### 4. 个人社交媒体

- **Twitter/X**: `https://twitter.com/{handle}` — 头像通常是高清个人照
- **Instagram**: `https://instagram.com/{handle}` — 精选照片
- 注意：社交媒体图片可能变更频繁，建议优先使用维基或官网

## 添加图片到条目

### 方法一：使用 YAML frontmatter + img 标签

在文件开头 `---` 后添加 `thumbnail:` 字段，然后在 `# 标题` 后添加 `<img>` 标签：

```markdown
---
thumbnail: https://upload.wikimedia.org/wikipedia/commons/.../xxx.jpg
---

# 女优名

<img src="https://upload.wikimedia.org/wikipedia/commons/.../xxx.jpg" alt="女优名" class="actress-photo" style="float: right; max-width: 280px; margin-left: 20px; border-radius: 8px;" />

## 基本信息
```

### 方法二：批量处理

使用 `scripts/add_image_display.py` 脚本可以自动为已有 `thumbnail:` 字段的文件添加 `<img>` 标签。
