from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup


@dataclass(slots=True)
class PageData:
    url: str
    language: str | None
    title: str | None
    meta_description: str | None
    canonical: str | None
    robots_meta: str
    h1: list[str]
    headings: list[tuple[str, str]]
    text: str
    cjk_chars: int
    latin_words: int
    images_total: int
    images_missing_alt: int
    internal_links: list[str]
    external_links: list[str]
    hreflang: list[tuple[str, str]]
    schema_types: list[str]
    schema_errors: list[str]
    og: dict[str, str]
    twitter: dict[str, str]
    has_author: bool
    has_date: bool
    list_count: int
    table_count: int
    question_heading_count: int
    links: list[tuple[str, str]] = field(default_factory=list)


def _content(soup: BeautifulSoup, selector: str, attribute: str = "content") -> str | None:
    node = soup.select_one(selector)
    if not node:
        return None
    value = node.get(attribute)
    if value:
        return str(value).strip()
    return None


def _schema_types(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        kind = value.get("@type")
        if isinstance(kind, str):
            found.append(kind)
        elif isinstance(kind, list):
            found.extend(str(item) for item in kind)
        for nested in value.values():
            found.extend(_schema_types(nested))
    elif isinstance(value, list):
        for item in value:
            found.extend(_schema_types(item))
    return found


def parse_page(html: str, url: str) -> PageData:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    description = _content(soup, 'meta[name="description" i]')
    canonical = _content(soup, 'link[rel~="canonical" i]', "href")
    if canonical:
        canonical = urljoin(url, canonical)
    robots_meta = " ".join(
        filter(
            None,
            [
                _content(soup, 'meta[name="robots" i]'),
                _content(soup, 'meta[name="googlebot" i]'),
            ],
        )
    ).lower()

    h1 = [node.get_text(" ", strip=True) for node in soup.find_all("h1")]
    headings = [
        (node.name.lower(), node.get_text(" ", strip=True))
        for node in soup.find_all(re.compile(r"^h[1-6]$"))
    ]
    question_headings = sum(
        1
        for _, text in headings
        if text.endswith(("?", "？"))
        or re.search(r"\b(what|why|how|when|where|which|can|does|is)\b", text, re.I)
        or any(token in text for token in ("什么", "如何", "为什么", "怎么", "哪些", "是否"))
    )

    images = soup.find_all("img")
    missing_alt = sum(1 for image in images if image.get("alt") is None)
    origin = urlsplit(url).netloc.lower()
    internal: list[str] = []
    external: list[str] = []
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        if not href or href.startswith(("#", "javascript:", "tel:")):
            continue
        absolute = urljoin(url, href)
        text_value = anchor.get_text(" ", strip=True)
        links.append((text_value, absolute))
        if absolute.startswith("mailto:"):
            continue
        if urlsplit(absolute).netloc.lower() == origin:
            internal.append(absolute)
        elif urlsplit(absolute).scheme in {"http", "https"}:
            external.append(absolute)

    hreflang = [
        (str(node.get("hreflang", "")).strip(), urljoin(url, str(node.get("href", ""))))
        for node in soup.select('link[rel~="alternate"][hreflang][href]')
    ]
    schema_types: list[str] = []
    schema_errors: list[str] = []
    for index, node in enumerate(soup.select('script[type="application/ld+json"]'), start=1):
        raw = node.string or node.get_text()
        if not raw.strip():
            continue
        try:
            schema_types.extend(_schema_types(json.loads(raw)))
        except (json.JSONDecodeError, TypeError) as exc:
            schema_errors.append(f"JSON-LD #{index} 无法解析：{exc}")

    for node in soup(["script", "style", "noscript", "template", "svg"]):
        node.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    cjk_chars = len(re.findall(r"[\u3400-\u9fff]", text))
    latin_words = len(re.findall(r"\b[\w'-]+\b", re.sub(r"[\u3400-\u9fff]", " ", text)))

    og = {
        key: value
        for key in ("title", "description", "image", "url", "type")
        if (value := _content(soup, f'meta[property="og:{key}" i]'))
    }
    twitter = {
        key: value
        for key in ("card", "title", "description", "image")
        if (value := _content(soup, f'meta[name="twitter:{key}" i]'))
    }
    language = str(soup.html.get("lang", "")).strip() if soup.html else None
    author_markers = bool(
        soup.select_one('[rel="author"], [itemprop="author"], meta[name="author" i], .author, .byline')
    )
    date_markers = bool(
        soup.select_one(
            "time[datetime], [itemprop='datePublished'], "
            "meta[property='article:published_time'], meta[property='article:modified_time']"
        )
    )

    return PageData(
        url=url,
        language=language or None,
        title=title,
        meta_description=description,
        canonical=canonical,
        robots_meta=robots_meta,
        h1=h1,
        headings=headings,
        text=text,
        cjk_chars=cjk_chars,
        latin_words=latin_words,
        images_total=len(images),
        images_missing_alt=missing_alt,
        internal_links=sorted(set(internal)),
        external_links=sorted(set(external)),
        hreflang=hreflang,
        schema_types=sorted(set(schema_types)),
        schema_errors=schema_errors,
        og=og,
        twitter=twitter,
        has_author=author_markers,
        has_date=date_markers,
        list_count=len(soup.find_all(["ul", "ol"])),
        table_count=len(soup.find_all("table")),
        question_heading_count=question_headings,
        links=links,
    )
