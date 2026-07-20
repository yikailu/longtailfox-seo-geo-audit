from __future__ import annotations

import re
import urllib.robotparser
from urllib.parse import urlsplit

from .fetcher import FetchResult
from .models import CheckResult
from .page import PageData


def _check(
    check_id: str,
    name: str,
    dimension: str,
    section: str,
    status: str,
    weight: float,
    evidence: list[str],
    impact: str,
    recommendation: str | None,
    *,
    url: str | None = None,
    confidence: str = "high",
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        name=name,
        dimension=dimension,  # type: ignore[arg-type]
        section=section,
        status=status,  # type: ignore[arg-type]
        weight=weight,
        evidence=evidence,
        impact=impact,
        recommendation=recommendation,
        confidence=confidence,
        url=url,
    )


def robots_allowed(robots_text: str, url: str, agent: str) -> bool:
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(url)
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(agent, url)


def site_checks(
    *,
    home: FetchResult,
    page: PageData | None,
    robots: FetchResult,
    sitemap_urls: list[str],
    sitemap_errors: list[str],
) -> list[CheckResult]:
    target_url = home.final_url or home.requested_url
    checks: list[CheckResult] = []
    https = urlsplit(target_url).scheme == "https"
    checks.append(
        _check(
            "seo.https",
            "HTTPS",
            "seo",
            "技术与抓取",
            "pass" if https else "fail",
            6,
            [f"最终 URL：{target_url}"],
            "HTTPS 是用户信任、传输安全和现代搜索体验的基础。",
            None if https else "全站启用 HTTPS，并将 HTTP 永久重定向至唯一 HTTPS 版本。",
            url=target_url,
        )
    )

    if robots.ok:
        checks.append(
            _check(
                "seo.robots",
                "robots.txt",
                "seo",
                "技术与抓取",
                "pass",
                5,
                [f"{robots.final_url} 返回 HTTP {robots.status_code}"],
                "robots.txt 可表达抓取策略和 Sitemap 位置。",
                None,
                url=robots.final_url,
            )
        )
    else:
        checks.append(
            _check(
                "seo.robots",
                "robots.txt",
                "seo",
                "技术与抓取",
                "warn" if robots.status_code == 404 else "error",
                5,
                [robots.error or f"HTTP {robots.status_code}"],
                "缺少 robots.txt 通常不等于禁止抓取，但会失去集中管理能力。",
                "提供可访问的 robots.txt，并声明规范 Sitemap URL。",
                url=robots.requested_url,
            )
        )

    sitemap_status = "pass" if sitemap_urls else ("error" if sitemap_errors else "warn")
    sitemap_evidence = (
        [f"解析到 {len(sitemap_urls)} 个唯一 URL"]
        if sitemap_urls
        else (sitemap_errors[:2] or ["未发现可解析的 Sitemap URL"])
    )
    checks.append(
        _check(
            "seo.sitemap",
            "XML Sitemap",
            "seo",
            "技术与抓取",
            sitemap_status,
            7,
            sitemap_evidence,
            "Sitemap 帮助搜索引擎发现重要页面并理解站点结构。",
            None if sitemap_urls else "生成 XML Sitemap，在 robots.txt 和站长平台中提交。",
            url=target_url,
        )
    )

    text = robots.text if robots.ok else ""
    for agent, label in (("Googlebot", "Googlebot"), ("Bingbot", "Bingbot")):
        allowed = robots_allowed(text, target_url, agent)
        checks.append(
            _check(
                f"seo.{agent.lower()}_access",
                f"{label} 抓取权限",
                "seo",
                "技术与抓取",
                "pass" if allowed else "fail",
                8,
                [f"robots.txt 对 {agent} 的结果：{'允许' if allowed else '禁止'}"],
                "基础搜索抓取权限直接影响页面被发现和进入索引的资格。",
                None if allowed else f"检查并移除对 {agent} 的非预期 Disallow 规则。",
                url=target_url,
            )
        )

    oai_allowed = robots_allowed(text, target_url, "OAI-SearchBot")
    checks.append(
        _check(
            "geo.oai_searchbot_access",
            "ChatGPT 搜索抓取权限",
            "geo",
            "AI 搜索可发现性",
            "pass" if oai_allowed else "fail",
            10,
            [f"robots.txt 对 OAI-SearchBot 的结果：{'允许' if oai_allowed else '禁止'}"],
            "OAI-SearchBot 抓取权限是内容进入 ChatGPT 搜索摘要与引用的基础条件之一。",
            None if oai_allowed else "如希望进入 ChatGPT 搜索，允许 OAI-SearchBot 抓取公开内容。",
            url=target_url,
        )
    )
    gpt_allowed = robots_allowed(text, target_url, "GPTBot")
    checks.append(
        _check(
            "geo.gptbot_policy",
            "GPTBot 训练偏好",
            "geo",
            "AI 内容策略",
            "info",
            0,
            [f"robots.txt 对 GPTBot 的结果：{'允许' if gpt_allowed else '禁止'}"],
            "GPTBot 与 ChatGPT 搜索抓取用途不同；允许或禁止属于内容训练政策选择。",
            "根据品牌内容政策决定是否允许 GPTBot，不把此项当作 GEO 排名因素。",
            url=target_url,
        )
    )

    if page:
        checks.extend(_trust_checks(page))
    return checks


def _trust_checks(page: PageData) -> list[CheckResult]:
    combined = [(text.lower(), url.lower()) for text, url in page.links]
    rules = [
        ("about", "关于我们", ("about", "company", "关于", "品牌"), 4),
        ("contact", "联系渠道", ("contact", "support", "mailto:", "联系", "客服"), 5),
        ("privacy", "隐私政策", ("privacy", "隐私"), 5),
        ("terms", "服务条款", ("terms", "conditions", "条款", "协议"), 4),
    ]
    checks: list[CheckResult] = []
    for key, name, markers, weight in rules:
        matches = [
            url
            for text, url in combined
            if any(marker in text or marker in url for marker in markers)
        ]
        status = "pass" if matches else "warn"
        checks.append(
            _check(
                f"seo.trust_{key}",
                name,
                "seo",
                "信任与透明度",
                status,
                weight,
                [f"首页发现入口：{matches[0]}"] if matches else [f"首页未发现明确的{name}入口"],
                "清晰的主体、联系和政策信息有助于用户与搜索系统验证网站身份。",
                None if matches else f"在主导航或页脚提供清晰可访问的{name}入口。",
                url=page.url,
                confidence="medium",
            )
        )
    return checks


def infer_page_type(page: PageData) -> str:
    path = urlsplit(page.url).path.lower()
    schema = {item.lower() for item in page.schema_types}
    if {"article", "blogposting", "newsarticle"} & schema or any(
        token in path for token in ("/blog/", "/article/", "/news/")
    ):
        return "article"
    if "product" in schema or "/product" in path:
        return "product"
    if "faqpage" in schema or "faq" in path:
        return "faq"
    if path in {"", "/"}:
        return "homepage"
    return "landing"


def page_checks(page: PageData, final_url: str, status_code: int | None) -> list[CheckResult]:
    checks: list[CheckResult] = []
    page_type = infer_page_type(page)

    if status_code and 200 <= status_code < 300:
        http_status = "pass"
    elif status_code:
        http_status = "fail"
    else:
        http_status = "error"
    checks.append(
        _check(
            "seo.http_status",
            "页面 HTTP 状态",
            "seo",
            "页面基础",
            http_status,
            8,
            [f"HTTP {status_code}" if status_code else "未取得 HTTP 状态"],
            "成功响应是抓取、索引和用户访问的基础。",
            None if http_status == "pass" else "修复响应错误或重定向链，使规范页面稳定返回 200。",
            url=final_url,
        )
    )

    title_length = len(page.title or "")
    title_status = "fail" if not page.title else ("warn" if title_length < 8 or title_length > 80 else "pass")
    checks.append(
        _check(
            "seo.title",
            "Title 标题",
            "seo",
            "页面基础",
            title_status,
            7,
            [f"Title：{page.title or '缺失'}", f"Unicode 字符数：{title_length}"],
            "Title 帮助搜索结果表达页面主题；实际展示长度会随设备与查询变化。",
            None if title_status == "pass" else "提供独特、具体并与页面意图一致的 Title，避免机械套用固定字符数。",
            url=final_url,
        )
    )

    description_length = len(page.meta_description or "")
    description_status = (
        "fail"
        if not page.meta_description
        else ("warn" if description_length < 45 or description_length > 220 else "pass")
    )
    checks.append(
        _check(
            "seo.meta_description",
            "Meta Description",
            "seo",
            "页面基础",
            description_status,
            5,
            [f"Description：{page.meta_description or '缺失'}", f"Unicode 字符数：{description_length}"],
            "高质量描述可帮助搜索系统和用户理解页面价值，但搜索引擎可能按查询改写摘要。",
            None if description_status == "pass" else "写一段准确、页面专属且包含具体价值的信息摘要。",
            url=final_url,
        )
    )

    h1_status = "pass" if len(page.h1) == 1 else ("fail" if not page.h1 else "warn")
    checks.append(
        _check(
            "seo.h1",
            "H1 主题标题",
            "seo",
            "内容结构",
            h1_status,
            6,
            [f"H1 数量：{len(page.h1)}", *(page.h1[:2] or ["未发现 H1"])],
            "清晰的主标题帮助用户和机器快速识别页面主题。",
            None if h1_status == "pass" else "为页面保留一个清晰、自然且与主要意图一致的 H1。",
            url=final_url,
        )
    )

    canonical_status = "fail" if not page.canonical else (
        "pass" if page.canonical.rstrip("/") == final_url.rstrip("/") else "warn"
    )
    checks.append(
        _check(
            "seo.canonical",
            "Canonical",
            "seo",
            "技术与索引",
            canonical_status,
            7,
            [f"Canonical：{page.canonical or '缺失'}", f"最终 URL：{final_url}"],
            "Canonical 帮助合并重复 URL 信号并明确首选页面。",
            None if canonical_status == "pass" else "确认首选 URL；非重复页面通常使用自引用 Canonical。",
            url=final_url,
        )
    )

    noindex = "noindex" in page.robots_meta
    checks.append(
        _check(
            "seo.indexability",
            "索引控制",
            "seo",
            "技术与索引",
            "fail" if noindex else "pass",
            10,
            [f"robots meta：{page.robots_meta or '未设置限制'}"],
            "noindex 会阻止页面进入常规搜索索引。",
            None if not noindex else "若页面应参与搜索，移除 noindex 并检查响应头 X-Robots-Tag。",
            url=final_url,
        )
    )

    if page.schema_errors:
        schema_status = "fail"
        schema_evidence = page.schema_errors[:2]
        schema_fix = "修复无法解析的 JSON-LD，并用官方验证工具复查。"
    elif page.schema_types:
        schema_status = "pass"
        schema_evidence = [f"检测到类型：{', '.join(page.schema_types)}"]
        schema_fix = None
    else:
        schema_status = "warn"
        schema_evidence = ["未检测到 JSON-LD"]
        schema_fix = "仅在与可见内容一致时添加适合页面类型的结构化数据。"
    checks.append(
        _check(
            "seo.schema",
            "结构化数据",
            "seo",
            "机器可读信息",
            schema_status,
            6,
            schema_evidence,
            "有效且一致的结构化数据有助于搜索系统理解实体和页面类型。",
            schema_fix,
            url=final_url,
        )
    )

    if page.images_total == 0:
        image_status = "info"
        image_evidence = ["页面未检测到 img 元素"]
    else:
        ratio = page.images_missing_alt / page.images_total
        image_status = "pass" if ratio == 0 else ("warn" if ratio < 0.4 else "fail")
        image_evidence = [f"图片 {page.images_total} 张，缺少 alt {page.images_missing_alt} 张"]
    checks.append(
        _check(
            "seo.image_alt",
            "图片替代文本",
            "seo",
            "内容与无障碍",
            image_status,
            4,
            image_evidence,
            "有意义的 Alt 文本支持无障碍访问和图片内容理解。",
            None if image_status in {"pass", "info"} else "为传达信息的图片补充准确 Alt；装饰图使用空 Alt。",
            url=final_url,
        )
    )

    internal_status = "pass" if len(page.internal_links) >= 3 else "warn"
    checks.append(
        _check(
            "seo.internal_links",
            "内部链接",
            "seo",
            "内容结构",
            internal_status,
            5,
            [f"检测到 {len(page.internal_links)} 个唯一内部链接"],
            "上下文内链帮助发现相关页面并建立主题关系。",
            None if internal_status == "pass" else "从主体内容链接到相关产品、解决方案或深度内容。",
            url=final_url,
        )
    )

    social_fields = len(page.og)
    checks.append(
        _check(
            "seo.social_metadata",
            "社交分享元数据",
            "seo",
            "分享展示",
            "pass" if social_fields >= 4 and "image" in page.og else "warn",
            3,
            [f"OG 字段：{', '.join(sorted(page.og)) or '无'}", f"Twitter 字段：{', '.join(sorted(page.twitter)) or '无'}"],
            "完整的分享元数据有助于外部传播时保持品牌和内容表达。",
            None if social_fields >= 4 and "image" in page.og else "补充 og:title、description、image、url、type 及 Twitter Card。",
            url=final_url,
        )
    )

    snippet_blocked = "nosnippet" in page.robots_meta or bool(
        re.search(r"max-snippet\s*:\s*0", page.robots_meta)
    )
    checks.append(
        _check(
            "geo.snippet_eligibility",
            "搜索摘要与引用资格",
            "geo",
            "AI 搜索可发现性",
            "fail" if noindex or snippet_blocked else "pass",
            10,
            [f"robots meta：{page.robots_meta or '未设置限制'}"],
            "noindex 或禁止摘要会限制页面作为搜索与生成式答案支持链接的资格。",
            None if not (noindex or snippet_blocked) else "根据内容政策调整 noindex、nosnippet 或 max-snippet 控制。",
            url=final_url,
        )
    )

    entity_types = {"Organization", "Corporation", "LocalBusiness", "Product", "Person", "WebSite"}
    present_entities = sorted(entity_types.intersection(page.schema_types))
    entity_status = "pass" if present_entities else "warn"
    checks.append(
        _check(
            "geo.entity_clarity",
            "实体清晰度",
            "geo",
            "实体与品牌",
            entity_status,
            9,
            [f"实体类型：{', '.join(present_entities) or '未检测到明确实体 Schema'}"],
            "明确、前后一致的品牌与产品实体有助于机器建立网站、组织和主题之间的关系。",
            None if present_entities else "在可见品牌信息一致的前提下完善 Organization/WebSite/Product 等 Schema。",
            url=final_url,
        )
    )

    text_pass = page.cjk_chars >= 180 or page.latin_words >= 80
    text_warn = page.cjk_chars >= 80 or page.latin_words >= 30
    text_status = "pass" if text_pass else ("warn" if text_warn else "fail")
    checks.append(
        _check(
            "geo.text_accessibility",
            "关键信息文本化",
            "geo",
            "内容可理解性",
            text_status,
            8,
            [f"可见中文字符约 {page.cjk_chars}，其他词约 {page.latin_words}"],
            "公开、可抓取的文本是搜索与生成式系统检索事实的基础。",
            None if text_status == "pass" else "把核心产品、适用场景、限制和差异点以可见 HTML 文本表达。",
            url=final_url,
        )
    )

    answer_signals = (
        min(page.question_heading_count, 2)
        + min(page.list_count, 2)
        + min(page.table_count, 1)
    )
    answer_status = "pass" if answer_signals >= 3 else ("warn" if answer_signals else "fail")
    checks.append(
        _check(
            "geo.answerability",
            "内容可回答性",
            "geo",
            "内容可理解性",
            answer_status,
            8,
            [
                f"问题式标题 {page.question_heading_count} 个",
                f"列表 {page.list_count} 个，表格 {page.table_count} 个",
            ],
            "清晰定义、步骤、列表和比较结构更容易支持用户问题和准确引用。",
            None if answer_status == "pass" else "按真实用户问题组织定义、步骤、比较或 FAQ；避免为 AI 机械切碎内容。",
            url=final_url,
        )
    )

    evidence_signals = int(page.has_author) + int(page.has_date) + int(bool(page.external_links))
    if re.search(r"\d+(?:[.,]\d+)?\s*(?:%|倍|年|月|天|hours?|days?)", page.text, re.I):
        evidence_signals += 1
    evidence_status = "pass" if evidence_signals >= 3 else ("warn" if evidence_signals else "fail")
    checks.append(
        _check(
            "geo.citeability",
            "内容可引用性",
            "geo",
            "信任与引用",
            evidence_status,
            9,
            [
                f"作者标识：{'有' if page.has_author else '无'}",
                f"日期标识：{'有' if page.has_date else '无'}",
                f"外部来源链接：{len(page.external_links)}",
            ],
            "作者、日期、数据、示例和来源能提高事实可验证性及引用价值。",
            None if evidence_status == "pass" else "补充真实作者、更新时间、原创数据或可核查来源；不要制造虚假引用。",
            url=final_url,
        )
    )

    if page_type == "article":
        freshness_status = "pass" if page.has_date else "warn"
        freshness_evidence = [f"文章日期标识：{'有' if page.has_date else '无'}"]
        freshness_fix = None if page.has_date else "显示发布日期和最后更新时间，并定期复核事实。"
    else:
        freshness_status = "info"
        freshness_evidence = [f"页面类型：{page_type}，不强制文章日期"]
        freshness_fix = None
    checks.append(
        _check(
            "geo.freshness",
            "内容新鲜度线索",
            "geo",
            "信任与引用",
            freshness_status,
            4,
            freshness_evidence,
            "对时效敏感内容，清楚日期有助于判断信息是否仍然适用。",
            freshness_fix,
            url=final_url,
        )
    )

    language_status = "pass" if page.language else "warn"
    checks.append(
        _check(
            "geo.language_signal",
            "页面语言信号",
            "geo",
            "多语言",
            language_status,
            4,
            [f"html lang：{page.language or '缺失'}", f"hreflang 数量：{len(page.hreflang)}"],
            "明确语言信号帮助搜索与生成式系统选择正确市场和语言版本。",
            None if page.language else "为每个语言页面设置准确 html lang，并让 hreflang、Canonical、Schema 语言一致。",
            url=final_url,
        )
    )
    return checks
