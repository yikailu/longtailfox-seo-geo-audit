from __future__ import annotations

import requests

from .models import CheckResult


def pagespeed_check(url: str, api_key: str | None) -> CheckResult:
    if not api_key:
        return CheckResult(
            check_id="seo.pagespeed",
            name="PageSpeed 性能",
            dimension="seo",
            section="性能与体验",
            status="unverified",
            weight=8,
            evidence=["未配置 PageSpeed Insights API Key"],
            impact="缺少实验室性能数据时，无法确认加载和交互体验。",
            recommendation="配置 PAGESPEED_API_KEY 后重新运行；未检测不按失败计分。",
            confidence="low",
            url=url,
        )
    try:
        response = requests.get(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
            params={
                "url": url,
                "strategy": "mobile",
                "category": ["performance", "accessibility", "best-practices", "seo"],
                "key": api_key,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        categories = data["lighthouseResult"]["categories"]
        scores = {
            key: round(value.get("score", 0) * 100)
            for key, value in categories.items()
            if value.get("score") is not None
        }
        performance = scores.get("performance", 0)
        status = "pass" if performance >= 90 else ("warn" if performance >= 50 else "fail")
        return CheckResult(
            check_id="seo.pagespeed",
            name="PageSpeed 性能",
            dimension="seo",
            section="性能与体验",
            status=status,
            weight=8,
            evidence=[f"{key}: {value}" for key, value in scores.items()],
            impact="页面性能和可访问性影响用户体验，也会影响搜索表现与转化。",
            recommendation=None if status == "pass" else "根据 Lighthouse Opportunities 优先修复 LCP、阻塞资源和长任务。",
            url=url,
        )
    except Exception as exc:
        return CheckResult(
            check_id="seo.pagespeed",
            name="PageSpeed 性能",
            dimension="seo",
            section="性能与体验",
            status="error",
            weight=8,
            evidence=[f"PageSpeed API 执行失败：{exc}"],
            impact="本次无法确认页面性能，不代表页面性能已失败。",
            recommendation="检查 API Key、配额和目标网站可访问性后重试。",
            confidence="low",
            url=url,
        )
