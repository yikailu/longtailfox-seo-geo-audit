from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlsplit

from defusedxml import ElementTree as ET

from .fetcher import FetchResult, safe_fetch


def sitemap_locations(xml_text: str) -> tuple[str, list[str]]:
    root = ET.fromstring(xml_text)
    kind = root.tag.rsplit("}", 1)[-1].lower()
    locations = [
        (node.text or "").strip()
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1].lower() == "loc" and (node.text or "").strip()
    ]
    return kind, locations


def discover_sitemap_urls(robots_text: str, origin: str) -> list[str]:
    found = []
    for line in robots_text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() == "sitemap" and value.strip():
            found.append(value.strip())
    found.extend([f"{origin}/sitemap.xml", f"{origin}/sitemap_index.xml"])
    return list(dict.fromkeys(found))


def load_sitemap(
    candidates: list[str],
    *,
    max_urls: int = 5_000,
    max_children: int = 10,
) -> tuple[list[str], list[FetchResult], list[str]]:
    urls: list[str] = []
    fetches: list[FetchResult] = []
    errors: list[str] = []
    for candidate in candidates:
        result = safe_fetch(candidate, max_bytes=5_000_000)
        fetches.append(result)
        if not result.ok:
            continue
        try:
            kind, locations = sitemap_locations(result.text)
        except Exception as exc:
            errors.append(f"{candidate}: Sitemap XML 解析失败：{exc}")
            continue
        if kind == "sitemapindex":
            for child in locations[:max_children]:
                child_result = safe_fetch(child, max_bytes=5_000_000)
                fetches.append(child_result)
                if not child_result.ok:
                    errors.append(f"{child}: 子 Sitemap 无法获取")
                    continue
                try:
                    _, child_locations = sitemap_locations(child_result.text)
                    urls.extend(child_locations)
                except Exception as exc:
                    errors.append(f"{child}: 子 Sitemap 解析失败：{exc}")
                if len(urls) >= max_urls:
                    break
        else:
            urls.extend(locations)
        if urls:
            break
    return list(dict.fromkeys(urls))[:max_urls], fetches, errors


def inventory(urls: list[str]) -> list[dict[str, object]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for url in urls:
        segments = [part for part in urlsplit(url).path.split("/") if part]
        path = f"/{segments[0]}/" if segments else "/"
        groups[path].append(url)
    hints = {
        "blog": "博客/内容",
        "articles": "博客/内容",
        "news": "新闻",
        "product": "产品",
        "products": "产品",
        "features": "产品功能",
        "solutions": "解决方案",
        "use-cases": "使用场景",
        "docs": "文档",
        "help": "帮助中心",
        "compare": "比较",
        "alternatives": "替代方案",
        "pricing": "定价",
    }
    result = []
    for path, members in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        key = path.strip("/").lower()
        result.append(
            {
                "directory": path,
                "url_count": len(members),
                "page_type": hints.get(key, "其他页面"),
                "example_url": members[0],
            }
        )
    return result


def representative_urls(urls: list[str], home_url: str, max_pages: int) -> list[str]:
    if max_pages <= 1:
        return [home_url]
    origin = urlsplit(home_url).netloc.lower()
    selected = [home_url]
    seen_directories: set[str] = set()
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != origin:
            continue
        segments = [part for part in parsed.path.split("/") if part]
        directory = segments[0].lower() if segments else "/"
        if directory in seen_directories:
            continue
        seen_directories.add(directory)
        normalized_home = home_url.rstrip("/")
        if url.rstrip("/") != normalized_home:
            selected.append(url)
        if len(selected) >= max_pages:
            break
    return selected
