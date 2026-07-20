<p align="center">
  <img src="longtailfox-seo-geo-audit/assets/longtailfox-lockup.png" alt="长尾狐 Longtail Fox" width="280">
</p>

# 长尾狐 SEO/GEO 网站审计

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

PageSpeed Insights API 用于获取 Lighthouse 的性能、可访问性、最佳实践和 SEO 分数。Google 允许不带 Key 的低频调用，但自动化使用建议配置自己的 API Key。未配置时，长尾狐会把性能检查标记为“未验证”，不会按失败计分。

### 1. 创建 Google Cloud 项目

1. 登录 [Google Cloud Console](https://console.cloud.google.com/)。
2. 新用户先打开[项目创建页面](https://console.cloud.google.com/projectcreate)，创建一个项目；已有项目可以直接选用。
3. 确认页面顶部显示的是刚才选择的项目。

### 2. 启用 PageSpeed Insights API

打开 [PageSpeed Insights API 页面](https://console.cloud.google.com/apis/library/pagespeedonline.googleapis.com)，点击“启用”。

如果直达链接没有自动选中项目，也可以在 Google Cloud Console 中依次进入：

`API 和服务` → `库` → 搜索 `PageSpeed Insights API` → `启用`

### 3. 创建 API Key

1. 打开 [API 和服务 → 凭据](https://console.cloud.google.com/apis/credentials)。
2. 点击“创建凭据”，选择“API 密钥”。
3. 复制生成的 Key，并给它一个容易识别的名称，例如 `longtailfox-pagespeed`。

这里创建的是普通 API Key，不需要 OAuth Client ID 或服务账号。如果组织项目不允许创建 Key，请让项目管理员授予 API Key 管理权限。

### 4. 限制 API Key

不要长期使用没有限制的 Key。打开刚创建的 Key，至少完成以下设置：

- `API 限制`：选择“限制密钥”，只勾选 `PageSpeed Insights API`。
- `应用限制`：
  - 在固定服务器上运行时，选择“IP 地址”，填写服务器的公网出口 IP。
  - 在个人电脑上运行且公网 IP 经常变化时，可以暂不限制来源，但应只把 Key 保存在本机环境变量中，并定期更换。

修改限制后保存。如果立即测试失败，可以等待几分钟再试。

### 5. 配置到长尾狐 Skill

推荐使用环境变量，避免 Key 出现在命令历史中。

macOS、Linux：

```bash
export PAGESPEED_API_KEY="替换为你的_API_Key"

python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com
```

Windows PowerShell：

```powershell
$env:PAGESPEED_API_KEY = "替换为你的_API_Key"

python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com
```

也可以只为一次审计传入 Key：

```bash
python longtailfox-seo-geo-audit/scripts/run-audit.py https://example.com \
  --pagespeed-api-key "替换为你的_API_Key"
```

这种方式可能把 Key 留在终端历史中，因此不建议在共享电脑或服务器上使用。

### 6. 验证 API Key

运行下面的命令。成功时会返回 JSON，其中包含 `lighthouseResult`：

```bash
curl --get \
  --header "x-goog-api-key: ${PAGESPEED_API_KEY}" \
  --data-urlencode "url=https://www.example.com/" \
  --data "strategy=mobile" \
  --data "category=performance" \
  "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
```

长尾狐默认使用移动设备策略，并读取以下 Lighthouse 分类：

- Performance
- Accessibility
- Best Practices
- SEO

性能分数达到 90 记为通过，50–89 记为警告，低于 50 记为失败。同一个页面在不同时间运行时可能出现小幅波动，这是 Lighthouse 测试环境和网站实时状态变化造成的。

### 常见问题

- `API key not valid`：Key 复制不完整、已删除，或尚未生效。
- `API has not been used` / `API is disabled`：当前项目没有启用 PageSpeed Insights API。
- `PERMISSION_DENIED`：API 限制或来源 IP 限制与当前请求不匹配。
- 无法创建或限制 Key：当前账号缺少项目权限，请联系项目管理员。
- `429` / `RESOURCE_EXHAUSTED`：项目配额已用完。可在 Google Cloud Console 的“API 和服务 → 配额”中查看使用量。
- 请求超时：目标网页无法被 Google 访问、加载时间过长，或 PageSpeed 服务暂时繁忙。

不要把 API Key 提交到 GitHub、写入 README 或发到公开聊天中。如果 Key 已经泄露，请立即在 Google Cloud Console 中轮换或删除。

Google 官方资料：

- [PageSpeed Insights API 入门](https://developers.google.com/speed/docs/insights/v5/get-started)
- [PageSpeed Insights API v5 方法说明](https://developers.google.com/speed/docs/insights/rest/v5/pagespeedapi/runpagespeed)
- [Google Cloud API Key 管理与限制](https://cloud.google.com/docs/authentication/api-keys)

## 报告边界

审计只使用生成时能够公开访问的网站信号。报告不能替代 GSC、Bing Webmaster Tools、服务器日志或商业数据，也不保证搜索引擎收录、排名或 AI 引用。

## 长尾狐

长尾狐提供内容规划、多语言写作、站内优化、外链匹配与效果追踪服务。

[访问 longtailfox.com](https://longtailfox.com/)

## License

代码使用 MIT License。Longtail Fox、长尾狐及 Logo 为品牌标识，MIT License 不授予商标使用权。
