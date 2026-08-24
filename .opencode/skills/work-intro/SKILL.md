---
name: work-intro
description: 获取 AV 作品的日语官方简介并写入 src/作品/ 页面（保留日文原文 + 添加中文翻译）。当用户要求为某番号补充简介、翻译作品介绍，或提到从 missAV/FANZA 获取作品介绍时使用。
---

# 获取作品日文简介并写入页面

目标：为 `src/作品/<番号>.md` 补充「日文原文 + 中文翻译」的官方简介。

## 页面格式约定

在 `## 简介` 或正文末尾、`## 参考资料` 之前插入：

```markdown
### 日文原文

> <日文简介原文>

### 中文翻译

<中文译文>
```

若该页没有 `## 参考资料`，则追加一段：

```markdown
## 参考资料

- [missAV 页面](https://missav.ws/ja/<番号小写>)
```

注意：`### 日文原文` 前必须有空行，避免与前一行内容粘连。

## 获取渠道（按优先级尝试）

1. **FANZA GraphQL API**（首选，无需认证；missAV 的日文简介即来源于此）
   ```sh
   curl -s -A "Mozilla/5.0" -H "Content-Type: application/json" \
     -d '{"query":"query { ppvContent(id:\"<cid>\"){ id title description } }"}' \
     https://api.video.dmm.co.jp/graphql
   ```
   - cid 规则：`番号前缀 + 数字部分补零到 5 位` 并转小写，如 `EBOD-613 → ebod00613`。
   - 部分厂商 cid 需加前缀：依次尝试 `1`、`h_086` 等，如 `SDDE-704 → 1sdde00704`。
   - 返回 `data.ppvContent: null` 表示已下架，转下一渠道。

2. **missAV（经 r.jina.ai 代理）**
   - 直接访问 missav.ws/.ai 会被 Cloudflare Turnstile 拦截，Playwright 也无法通过，不要浪费时间尝试直连。
   ```sh
   # 简介在 meta description 中（可能被 missAV 截断）
   curl -s -m 90 -H "X-Return-Format: html" \
     "https://r.jina.ai/https://missav.ws/ja/<番号小写>" \
     | grep -o '<meta name="description" content="[^"]*"'
   ```
   - 注意 `description` 为空说明该页无简介。

3. **镜像/聚合站**（下架作品的完整文案来源）
   - DUGA：`https://duga.jp/search/<番号>/` 找到 `ppv/<id>` 页面，其中「作品紹介」为完整官方文案。
   - jav321：`https://www.jav321.com/video/<cid>`（可经 r.jina.ai 代理），正文含完整日文简介。
   - MGS：`https://www.mgstage.com/product/product_detail/<番号>/` 有年龄墙，需 cookie 或代理。
   - 也可用 websearch 搜「番号 + 紹介文 / 作品紹介」定位。

## 写入规则

- 简介原文必须原样保留（包括 ○● 隐字符、片假名等），不得改写。
- 中文翻译由助手自行翻译，语气贴近原文的口语/宣传风格。
- 若作品本身是中文发音作品（如 SOD 中文企划），保留原文并注明「无需翻译」。
- 若来源不是 FANZA/missAV，在末尾用引用块注明：
  `> 注：该作品已从 FANZA 下架，以上文案取自 <来源>。`
- 写完后运行 `git diff` 检查：只应有新增行，且 `### 日文原文` 标题独立成行。

## 已知坑

- 插入文本时若目标文件没有 `## 参考资料`，不要用「查找该标题」定位插入点（会得到 -1 导致内容粘连），应直接在文件末尾追加。
- FANZA API introspection 被禁用；字段名可利用 GraphQL 校验报错的 "Did you mean" 提示探测。
