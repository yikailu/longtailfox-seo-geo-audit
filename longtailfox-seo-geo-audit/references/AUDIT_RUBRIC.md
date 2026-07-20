# 审计评分规则

## 目录

1. 状态
2. 评分
3. SEO 检查
4. GEO 检查
5. 多语言与中文规则
6. 建议优先级

## 状态

| 状态 | 含义 | 计分 |
|---|---|---:|
| `pass` | 已验证满足要求 | 100% |
| `warn` | 已验证存在改进空间 | 50% |
| `fail` | 已验证存在明确问题 | 0% |
| `info` | 政策选择或背景信息 | 不计分 |
| `unverified` | 缺少必要数据 | 不计分 |
| `error` | 检查执行失败 | 不计分 |

每个非 `info` 检查都必须带权重。SEO 和 GEO 分开归一化，避免同一信号重复夸大总分。

## 评分

- `SEO 就绪度 = 已验证 SEO 检查所得分 / 已验证 SEO 检查权重`
- `GEO 就绪度 = 已验证 GEO 检查所得分 / 已验证 GEO 检查权重`
- `证据覆盖率 = 已验证检查权重 / 全部应执行检查权重`

报告不生成一个掩盖差异的总分。覆盖率低于 60% 时，在摘要中提示结论置信度有限。

## SEO 检查

站点级：

- HTTPS、HTTP 状态与安全重定向；
- robots.txt、Sitemap 及主要目录盘点；
- Googlebot/Bingbot 可抓取性；
- Canonical、索引与摘要控制；
- 404、测试站、hreflang 和多语言一致性；
- About、Contact、Privacy、Terms 等信任入口；
- 可选 PageSpeed。

页面级：

- Title、Meta Description、H1、标题结构；
- Canonical、自引用与最终 URL；
- 主体文字、图片 Alt、内链；
- JSON-LD 可解析性、类型和可见内容一致性；
- OG/Twitter 分享信息。

字符长度只作为提示。不得仅因不在固定字符区间就判为严重失败。中文按 Unicode 字符和结构判断，英文按词与结构判断。

## GEO 检查

- Google/Bing 搜索索引资格；
- OAI-SearchBot 抓取权限；
- GPTBot 训练偏好作为 `info` 单独报告；
- `noindex`、`nosnippet`、`max-snippet` 等引用限制；
- 品牌、组织、产品、作者等实体是否清楚；
- Organization/Product/Article 等结构化信息是否与页面一致；
- 重要信息是否以可访问文本呈现；
- 定义、问题、步骤、列表、表格和比较结构；
- 原创经验、数据、示例、来源和作者信息；
- 发布/更新时间与内容维护线索；
- 平台可见性数据仅在用户提供时纳入。

不要把 `llms.txt` 或特殊 AI Schema 作为 Google AI 搜索必需项。

## 多语言与中文规则

- 保留原文证据，中文解释结论。
- 校验 `html[lang]`、hreflang、Canonical 和 Schema `inLanguage` 是否一致。
- 中文不得套用英文停用词和固定词数阈值。
- Unicode URL 不因非 ASCII 本身失败；仅检查可读性、层级和一致性。

## 建议优先级

按以下顺序排序：

1. 阻止抓取、索引或摘要展示的问题；
2. 错误 Canonical、重复版本和关键 Schema 错误；
3. 首页/核心页面缺失主题、信任或实体信息；
4. 内容可回答性、证据和内链；
5. 社交信息与非关键格式改进。

每条建议写明影响与工作量，不得承诺排名或 AI 引用。
