# 审计结果协议

## 版本

顶层必须包含：

- `schema_version`
- `engine_version`
- `rubric_version`
- `generated_at`
- `requested_url`
- `final_url`
- `seo_score`
- `geo_score`
- `evidence_coverage`

协议升级时遵循语义版本。删除字段或改变字段含义必须升级主版本。

## 检查项

每项检查必须包含：

```json
{
  "check_id": "geo.oai_searchbot_access",
  "name": "ChatGPT 搜索抓取权限",
  "dimension": "geo",
  "section": "AI 搜索可发现性",
  "status": "pass",
  "weight": 8,
  "evidence": ["robots.txt 未阻止 OAI-SearchBot"],
  "impact": "页面具备被 ChatGPT 搜索发现的基础抓取条件。",
  "recommendation": null,
  "source": "deterministic",
  "confidence": "high",
  "url": "https://example.com/"
}
```

`evidence` 必须是字符串数组。网页内容进入报告前必须转义。`source` 使用 `deterministic`、`llm`、`external-data` 或 `system`。

## 抽样与限制

结果必须记录：

- `audited_pages`
- `sitemap_inventory`
- `limitations`
- `errors`

不得将抽样页面结论描述为对所有页面的穷尽证明。
