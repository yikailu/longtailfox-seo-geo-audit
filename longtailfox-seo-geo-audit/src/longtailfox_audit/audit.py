from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlsplit

from . import __version__
from .checks import infer_page_type, page_checks, site_checks
from .fetcher import FetchResult, safe_fetch
from .models import AuditResult, CheckResult, PageSummary
from .page import parse_page
from .pagespeed import pagespeed_check
from .scoring import dimension_score, evidence_coverage
from .security import assert_public_url
from .sitemap import discover_sitemap_urls, inventory, load_sitemap, representative_urls

Progress = Callable[[str, int], None]


def _notify(callback: Progress | None, stage: str, percent: int) -> None:
    if callback:
        callback(stage, percent)


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _failed_home_check(url: str, result: FetchResult) -> CheckResult:
    return CheckResult(
        check_id="seo.home_fetch",
        name="首页可访问性",
        dimension="seo",
        section="页面基础",
        status="error" if result.status_code is None else "fail",
        weight=10,
        evidence=[result.error or f"HTTP {result.status_code}"],
        impact="无法取得首页时，站点和页面审计不能完整执行。",
        recommendation="检查 DNS、TLS、WAF、HTTP 状态和自动化访问策略后重试。",
        confidence="high",
        url=url,
    )


def run_audit(
    url: str,
    *,
    max_pages: int = 8,
    pagespeed_api_key: str | None = None,
    progress: Progress | None = None,
) -> AuditResult:
    max_pages = min(max(int(max_pages), 1), 20)
    requested = assert_public_url(url)
    generated = datetime.now(timezone.utc).isoformat()
    errors: list[str] = []
    limitations = [
        "结果基于生成时可公开访问的信号，不保证收录、排名或 AI 引用。",
        "未接入 GSC、Bing Webmaster Tools 或日志数据时，不包含真实曝光与引用次数。",
        f"本次最多抽样 {max_pages} 个代表页面，不等同于穷尽式全站爬取。",
    ]

    _notify(progress, "fetch_home", 5)
    home = safe_fetch(requested)
    if not home.ok or not home.final_url:
        failed = _failed_home_check(requested, home)
        return AuditResult(
            schema_version="1.0.0",
            engine_version=__version__,
            rubric_version="1.0.0",
            generated_at=generated,
            requested_url=requested,
            final_url=home.final_url,
            seo_score=None,
            geo_score=None,
            evidence_coverage=evidence_coverage([failed]),
            checks=[failed],
            audited_pages=[],
            sitemap_inventory=[],
            limitations=limitations,
            errors=[home.error or f"首页 HTTP {home.status_code}"],
        )

    final_home = home.final_url
    origin = _origin(final_home)
    home_page = parse_page(home.text, final_home)

    _notify(progress, "fetch_robots", 15)
    robots = safe_fetch(f"{origin}/robots.txt", max_bytes=1_000_000)
    candidates = discover_sitemap_urls(robots.text if robots.ok else "", origin)

    _notify(progress, "fetch_sitemap", 25)
    sitemap_urls, _, sitemap_errors = load_sitemap(candidates)
    errors.extend(sitemap_errors)
    site_inventory = inventory(sitemap_urls)
    samples = representative_urls(sitemap_urls, final_home, max_pages)

    checks = site_checks(
        home=home,
        page=home_page,
        robots=robots,
        sitemap_urls=sitemap_urls,
        sitemap_errors=sitemap_errors,
    )
    pages: list[PageSummary] = []
    for index, sample in enumerate(samples):
        _notify(progress, "audit_pages", 30 + round((index + 1) / len(samples) * 50))
        fetch = home if sample.rstrip("/") == final_home.rstrip("/") else safe_fetch(sample)
        if not fetch.ok or not fetch.final_url:
            errors.append(f"{sample}: {fetch.error or f'HTTP {fetch.status_code}'}")
            error_check = _failed_home_check(sample, fetch)
            error_check.check_id = "seo.page_fetch"
            error_check.name = "抽样页面可访问性"
            checks.append(error_check)
            pages.append(
                PageSummary(
                    url=sample,
                    final_url=fetch.final_url or sample,
                    status_code=fetch.status_code,
                    page_type="unknown",
                    language=None,
                    title=None,
                    checks=[error_check],
                )
            )
            continue
        parsed = home_page if fetch is home else parse_page(fetch.text, fetch.final_url)
        current_checks = page_checks(parsed, fetch.final_url, fetch.status_code)
        checks.extend(current_checks)
        pages.append(
            PageSummary(
                url=sample,
                final_url=fetch.final_url,
                status_code=fetch.status_code,
                page_type=infer_page_type(parsed),
                language=parsed.language,
                title=parsed.title,
                checks=current_checks,
            )
        )

    _notify(progress, "pagespeed", 85)
    key = pagespeed_api_key or os.getenv("PAGESPEED_API_KEY") or os.getenv("GOOGLE_PAGESPEED_API_KEY")
    checks.append(pagespeed_check(final_home, key))

    _notify(progress, "score", 95)
    result = AuditResult(
        schema_version="1.0.0",
        engine_version=__version__,
        rubric_version="1.0.0",
        generated_at=generated,
        requested_url=requested,
        final_url=final_home,
        seo_score=dimension_score(checks, "seo"),
        geo_score=dimension_score(checks, "geo"),
        evidence_coverage=evidence_coverage(checks),
        checks=checks,
        audited_pages=pages,
        sitemap_inventory=site_inventory,
        limitations=limitations,
        errors=errors,
        metadata={
            "max_pages": max_pages,
            "sitemap_url_count": len(sitemap_urls),
            "pagespeed_supplied": bool(key),
        },
    )
    _notify(progress, "complete", 100)
    return result
