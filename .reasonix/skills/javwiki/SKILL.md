# javwiki — JAV 百科编辑助手

## 概述

javwiki（`javwiki.github.io`）是一个基于 **mdBook** 的中文 JAV（日本成人视频）综合百科站点。本技能涵盖百科条目管理、数据采集、构建部署等完整工作流。

- **站点**: https://javwiki.github.io
- **源码目录**: `src/`
- **构建工具**: mdBook + mdbook-tagging + mdbook-summarizer
- **数据采集**: `scrapers/fanza/` — Playwright 爬虫

---

## 1. 添加女优条目

### 1.1 确定命名与位置

根据女优艺名的**读音首假名**确定存储路径，规则详见 [`src/_meta/五十音排序规则.md`](../../../src/_meta/五十音排序规则.md)：

**归类示例**：
| 女优 | 读音 | 首假名 | 行 | 段 |
|------|------|--------|----|-----|
| 河北彩花 | かわきた さいか | か | か行 | か段 |
| 相泽南 | あいざわ みなみ | あ | あ行 | あ段 |
| 深田咏美 | ふかだ えみ | ふ | は行 | ふ段 |
| ベアトリクス | べあとりくす | べ | は行 | べ段 |
| Miru | みる | み | ま行 | み段 |

**文件路径**: `src/{行}/{段}/{女优名}.md`

### 1.2 创建 Markdown 文件

模板：

```markdown
---
tags: [罩杯, 经纪公司, 片商]   # 如 tags: [E罩, T-POWERS, S1]
---

# 女优名

## 基本信息

- **姓名**: 中文名
- **日文名**: 日文原名
- **读音**: 假名读音
- **英文名**: 罗马音
- **出生日期**: YYYY年M月D日
- **出生地**: 日本某地
- **身高**: XXXcm
- **三围**: BXX WXX HXX
- **罩杯**: 字母
- **类别**: Censored（有码系）/ Uncensored（无码系）
- **活跃年代**: 年份
- **经纪公司**: 公司名
- **主要片商**: 片商名

## 简介

2-4 句概括性介绍。

## 人物

- 特点/亮点
- 兴趣爱好
- 特长
- 其他轶事

## 作品特征

- 风格描述
- 代表作类型

## 经历年表

| 年份 | 经历 |
| --- | --- |
| YYYY | 事件描述。 |

## 获奖记录

- YYYY年 XXX奖项

## 参考资料

- <https://zh.wikipedia.org/wiki/女优名>
- <https://ja.wikipedia.org/wiki/女优名>
- <https://www.wikidata.org/wiki/Q编号>
- <https://x.com/账号>  <!-- X/Twitter -->
- <https://www.instagram.com/账号>  <!-- Instagram -->
- 其他来源...
```

### 1.3 信息来源（优先级由高到低）

| 信息类型 | 推荐来源 | 备注 |
|---------|---------|------|
| 基本资料 | Wikipedia、JAVDB、Xslist | 以维基百科为主，交叉验证 |
| 三围/罩杯 | 厂商官网、JAVDB、minnano-av | 不同来源可能有差异 |
| 经纪公司 | Xslist、JAVDB、厂商官网 | 变动频繁，注意时效 |
| 专属片商 | 厂商官网、JAVDB | 以官网为准 |
| 出道日期 | Wikipedia、JAVDB、厂商官网 | 以出道作品发售日为准 |
| 引退/状态 | Twitter/X、Wikipedia、JAVDB | 以本人公开声明为准 |
| 获奖记录 | Wikipedia、FANZA 官网 | 以官方公布为准 |

完整来源列表见 [`src/_meta/source.md`](../../../src/_meta/source.md)

### 1.4 同步更新（必须！）

新增或修改女优条目后，必须同步以下三处：

1. **文件系统** — 条目文件 `src/{行}/{段}/{女优名}.md` ✓（已创建）
2. **行索引** — `src/{行}/index.md` 中添加链接
3. **段索引** — `src/{行}/{段}/index.md` 中添加链接

### 1.5 运行构建验证

```bash
# 确保已安装 mdbook-tagging 和 mdbook-summarizer
mdbook-summarizer --src src --auto-readme
mdbook-tagging generate .
mdbook build
```

检查构建无报错后提交。

---

## 2. 编辑女优条目

### 2.1 更新信息

直接编辑对应女优的 `.md` 文件，保持模板结构一致。

### 2.2 更新事件

若女优经历有更新（移籍、引退、复出等），在**经历年表**中追加新行。

### 2.3 更新标签

若经纪公司、专属片商或状态变化，同步更新 frontmatter 中的 `tags`。

### 2.4 资料缺失条目

见 [`src/_meta/todo.md`](../../../src/_meta/todo.md) 中记录的状态：

- **维基无条目** → 尝试 Seesaa Wiki、JAVDB、minnano-av、厂商官网
- **社交缺位** → X/Twitter、Instagram 搜索确认
- **基本信息缺失** → 优先补全姓名、出生日期、身高、三围等

---

## 3. 社交媒体管理

社交媒体是获取和验证女优最新动态的首要渠道，也是百科参考资料的重要组成部分。

### 3.1 主要平台

| 平台 | 用途 | 备注 |
|------|------|------|
| **X（Twitter）** | 官方公告、日常动态、活动信息 | 最优先来源，多数女优仍在使用 |
| **Instagram** | 写真、活动照片、生活分享 | 部分女优设有两个账号（公开/私密） |
| **YouTube** | 访谈、幕后花絮、日常vlog | 活跃女优通常会开设个人频道 |
| **Fantia** | 粉丝俱乐部、付费内容 | SOD Group 所属女优使用较多 |
| **TikTok** | 短视频、日常分享 | 年轻女优使用较多 |

完整社交来源列表见 [`src/_meta/source.md`](../../../src/_meta/source.md)「社交媒体」章节。

### 3.2 账号查找与验证

#### 查找方法

1. **Wikipedia 信息框（infobox）** — 日文/中文维基百科通常在右侧信息框中列出社交媒体账号
2. **经纪公司官网** — 经纪公司官网的女优介绍页通常附有社交媒体链接
3. **作品包装 / 厂商官网** — 部分厂商在作品页面提供女优的官方账号链接
4. **搜索引擎搜索** — 关键词：`女优名 Twitter` / `女优名 Instagram` 等
5. **交叉验证** — 从多个来源确认同一账号，避免冒名账号

#### 验证标准

| 验证项 | 说明 |
|--------|------|
| ✅ **官方账号** | 有官方认证标记（✓）、经纪公司官网链接确认、维基百科引用 |
| ✅ **粉丝数** | 粉丝数较高的账号通常更可靠（但也存在高仿号） |
| ✅ **内容一致性** | 账号内容与女优本人经历、作品信息一致 |
| ✅ **互关关系** | 关注列表中的同行女优、经纪公司、厂商官方账号可辅助验证 |
| ❌ **冒名账号** | 无本人照片、仅转发内容、链接到可疑网站 |

### 3.3 参考资料格式

在女优条目的**参考资料**章节中，按以下格式记录社交媒体：

```markdown
- <https://x.com/账号>  <!-- X/Twitter -->
- <https://www.instagram.com/账号>  <!-- Instagram -->
- <https://www.youtube.com/@频道ID>  <!-- YouTube -->
- <https://fantia.jp/fanclubs/数字ID>  <!-- Fantia -->
```

### 3.4 状态管理

| 状态 | 处理方式 | 示例 |
|------|---------|------|
| ✅ **账号活跃** | 正常记录在参考资料中 | `- <https://x.com/umi_sea_0v0>` |
| 🔒 **账号锁定/私密** | 仍可记录，标注「（私密账号）」 | `- <https://www.instagram.com/xxx>（私密账号）` |
| 🚫 **已删除/不存在** | 在 [`todo.md`](../../../src/_meta/todo.md) 的「社交媒体缺失」表中记录 | `社交媒体已删除` |
| ⏸️ **活动停止/引退** | 若账号仍存在则保留链接；若已删除则在 todo 中记录 | `2023年活动停止，社交媒体已删除` |
| 🔄 **账号更名** | 记录最新用户名，旧名可在备注中说明 | `原 @old_name` |

### 3.5 资料缺失时的处理

见 [`src/_meta/todo.md`](../../../src/_meta/todo.md) 的「社交媒体缺失」表：

- **暂未找到公开社交媒体** — 在各平台搜索确认后仍无结果，添加到 todo 表
- **引退/活动停止导致账号删除** — 标注「已删除」状态
- **不确定是否为本人账号** — 进一步交叉验证后再决定是否添加

### 3.6 注意事项

- 社交媒体信息变动频繁，编辑时注意时效性
- 优先使用女优本人的官方账号，其次是经纪公司代管的账号
- 引退女优的社交媒体如已删除，切勿使用存档链接冒充活跃状态
- 部分女优引退后主动删除社交媒体，这应得到尊重

---

## 4. 添加/编辑厂商（厂牌）

### 4.1 文件路径

`src/厂牌/{厂商名}.md`（URL 中的空格需编码为 `%20`）

### 4.2 模板

```markdown
# 厂商名

## 基本信息

- **简称**: XXX
- **所属**: 全称
- **特点**: 一句话概括

## 特点

- ...

## 知名女优

- ...

## 主要系列

- ...

## 参考资料

- 官网链接
```

---

## 5. 添加/编辑经纪公司

### 5.1 文件路径

`src/经纪公司/{公司名}.md`

### 5.2 模板

```markdown
# 公司名

- **全称**: 
- **特点**: 
- **业务**: 
- **知名女优**: 
```

---

## 6. 构建与本地预览（可选）

> 此步骤可选，仅在需要本地预览或调试构建时执行。日常编辑可直接推送 `main` 分支由 CI/CD 自动构建。

### 6.1 安装 mdBook 及插件

```bash
# 安装 mdBook
cargo install mdbook

# 安装插件
cargo install mdbook-summarizer
cargo install mdbook-tagging
```

### 6.2 构建

```bash
# 1. 自动生成 SUMMARY.md（基于目录结构）
mdbook-summarizer --src src --auto-readme

# 2. 生成标签索引页
mdbook-tagging generate .

# 3. 构建静态站点
mdbook build

# 构建输出在 book/ 目录
```

### 6.3 本地预览

```bash
mdbook serve --open
```

默认访问 http://localhost:3000

### 6.4 快速构建脚本

一键构建：

```bash
mdbook-summarizer --src src --auto-readme && mdbook-tagging generate . && mdbook build
```

---

## 7. 部署

### GitHub Pages 自动部署

推送到 `main` 分支后，GitHub Actions 自动完成构建与部署：

1. 安装 mdBook + mdbook-summarizer + mdbook-tagging
2. 运行 `mdbook-tagging generate .`
3. 运行 `mdbook-summarizer --src src --auto-readme`
4. 运行 `mdbook build`
5. 上传 `book/` 目录到 GitHub Pages

**工作流文件**: `.github/workflows/mdbook.yml`

也可在 GitHub 仓库 Actions 页面手动触发 `workflow_dispatch`。

---

## 8. 目录结构参考

```
javwiki.github.io/
├── book.toml                  # mdBook 配置
├── .github/workflows/mdbook.yml  # CI/CD
├── src/
│   ├── README.md              # 百科首页
│   ├── SUMMARY.md             # 自动生成的目录
│   ├── _meta/                 # 元信息
│   │   ├── index.md           # 参考资料
│   │   ├── source.md          # 信息来源清单
│   │   ├── todo.md            # 资料缺失女优
│   │   ├── 五十音排序规则.md    # 排序规则
│   │   ├── 术语.md            # 常见术语
│   │   ├── 厂商.md            # 厂商概览
│   │   ├── 经纪公司.md         # 经纪公司概览
│   │   ├── 企划.md            # 企划类型
│   │   ├── 番号.md            # 番号系统
│   │   ├── list.md            # 女优列表
│   │   ├── 奖项/              # 奖项资料
│   │   │   ├── fanza.md
│   │   │   ├── ADULTOPIA.md
│   │   │   └── skypa.md
│   │   ├── rankings/          # FANZA 排名数据
│   │   └── collection/        # 作品收藏
│   ├── {行}/                   # 五十音行（あ/か/さ/た/な/は/ま/や/ら/わ）
│   │   ├── index.md           # 行索引
│   │   └── {段}/              # 五十音段
│   │       ├── index.md       # 段索引
│   │       └── {女优名}.md    # 女优条目
│   ├── 作品/                  # 作品条目（待建设）
│   ├── 厂牌/                  # 厂商条目
│   ├── 导演/                  # 导演条目（待建设）
│   ├── 系列/                  # 系列条目（待建设）
│   ├── 经纪公司/              # 经纪公司条目
│   └── _tags/                 # 标签索引（自动生成）
│       └── README.md
├── scrapers/fanza/
│   ├── spider.py              # FANZA 排名爬虫
│   └── requirements.txt       # Python 依赖
└── book/                      # 构建输出（不提交）
```

---

## 附录：FANZA 月度排名

### 运行爬虫

```bash
cd scrapers/fanza
pip install -r requirements.txt
python spider.py --limit 100 --proxy socks5://127.0.0.1:7890
```

参数说明：
- `--limit`  — 获取条数（默认 100）
- `--proxy`  — 代理地址（默认 socks5://127.0.0.1:7890）
- `--output` — 输出目录（默认 `../../src/_meta/rankings`）

### 输出

数据保存为 `src/_meta/rankings/actress-ranking-YYYYMM.yaml`，内容结构：

```yaml
source: FANZA
type: actress_monthly_ranking
url: https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress
fetched_at: "YYYY-MM-DDTHH:MM:SS"
count: 100
rankings:
  - rank: 1
    actress_id: "xxx"
    name: "女优名"
    image: "https://..."
    contents_count: 50
    latest_content_id: "xxx"
    latest_title: "最新作品标题"
```

### 环境要求

- Python 3.9+
- 需要安装 Playwright 浏览器：`playwright install chromium`
- 需要代理访问日本网站

---

## 工作流速查表

| 任务 | 关键动作 | 验证方式 |
|------|---------|---------|
| 🆕 添加女优 | 创建 `.md` + 更新行/段索引 + 构建 | `mdbook build` 无报错 |
| ✏️ 编辑女优 | 编辑 `.md` + 可选更新 tags | - |
| 🔗 社交媒体管理 | 验证账号 → 记录参考资料 → 更新 todo | 多源交叉验证 |
| 🏭 添加厂商 | 创建 `src/厂牌/{名}.md` | `mdbook build` 无报错 |
| 🏢 添加经纪公司 | 创建 `src/经纪公司/{名}.md` | `mdbook build` 无报错 |
| 🔨 构建（可选） | `mdbook-summarizer && mdbook-tagging && mdbook build` | 无报错 |
| 🚀 部署 | 推送 `main` 分支 | GitHub Actions ✅ |
| 📊 附录：FANZA 排名 | 见附录 → 运行爬虫 | 输出 YAML 无报错 |
