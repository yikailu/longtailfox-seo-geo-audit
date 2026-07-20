<p align="center">
  <img src="longtailfox-seo-geo-audit/assets/longtailfox-lockup.png" alt="长尾狐 Longtail Fox" width="280">
</p>

# 长尾狐网站SEO/GEO专业审计

输入一个公开网站地址，生成中文 SEO/GEO 审计报告。报告包含结构化 JSON、独立 HTML，并可在本机安装 Chrome 或 Chromium 后输出 PDF。

## 检查内容

- robots.txt、XML Sitemap 与搜索引擎抓取权限
- Title、Meta Description、H1、Canonical、hreflang 与索引设置
- 图片、内链、结构化数据和社交分享标签
- Googlebot、Bingbot、OAI-SearchBot 与 GPTBot 访问策略
- 品牌实体清晰度、内容可回答性和可引用性
- SEO 就绪度、GEO 就绪度与证据覆盖率

## 安装

```bash
npx skills add https://github.com/yikailu/longtailfox-seo-geo-audit \
  --skill longtailfox-seo-geo-audit
```

安装完成后，可以直接向 Agent 提出：

> 使用长尾狐 SEO/GEO 审计检查 https://example.com，并生成中文报告。

## 命令行使用

需要 Python 3.11 或更高版本。

```bash
python -m pip install -r longtailfox-seo-geo-audit/requirements.txt
python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com
```

默认最多抽样 8 个代表页面，并在 `reports/` 目录生成：

- `<域名>-seo-geo-audit.json`
- `<域名>-seo-geo-audit.html`
- `<域名>-seo-geo-audit.pdf`（需要 Chrome 或 Chromium）

常用参数：

```bash
python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com \
  --max-pages 12 \
  --output-dir reports
```

## 配置 PageSpeed Insights API

如需在报告中加入 Lighthouse 分数，请先在 Google Cloud 中[启用 PageSpeed Insights API](https://console.cloud.google.com/apis/library/pagespeedonline.googleapis.com)，然后到[凭据页面](https://console.cloud.google.com/apis/credentials)创建 API Key。建议把 Key 的使用范围限制为 `PageSpeed Insights API`。

macOS、Linux 使用：
```bash
export PAGESPEED_API_KEY="替换为你的_API_Key"
python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com
```

Windows PowerShell 使用：
```powershell
$env:PAGESPEED_API_KEY = "替换为你的_API_Key"
python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com
```

也可以通过 `--pagespeed-api-key` 参数传入。未配置时，性能检查会标记为“未验证”，不会按失败计分。不要把 API Key 提交到 GitHub。

## 报告边界

审计只使用生成时能够公开访问的网站信号。报告不能替代 GSC、Bing Webmaster Tools、服务器日志或商业数据，也不保证搜索引擎收录、排名或 AI 引用。

## 长尾狐

长尾狐提供内容规划、多语言写作、站内优化、外链匹配与效果追踪服务。

[访问 longtailfox.com](https://longtailfox.com/)

## License

代码使用 MIT License。Longtail Fox、长尾狐及 Logo 为品牌标识，MIT License 不授予商标使用权。
