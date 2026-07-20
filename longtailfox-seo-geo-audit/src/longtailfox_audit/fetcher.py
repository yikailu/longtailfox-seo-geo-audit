from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import requests

from .security import UnsafeUrlError, assert_public_url

USER_AGENT = "LongtailFoxAuditBot/0.1 (+https://longtailfox.com/)"


@dataclass(slots=True)
class FetchResult:
    requested_url: str
    final_url: str | None
    status_code: int | None
    headers: dict[str, str]
    text: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.status_code and 200 <= self.status_code < 300 and not self.error)


def safe_fetch(
    url: str,
    *,
    timeout: float = 15,
    max_bytes: int = 3_000_000,
    max_redirects: int = 5,
    session: requests.Session | None = None,
) -> FetchResult:
    requested = url
    client = session or requests.Session()
    current = url
    for _ in range(max_redirects + 1):
        try:
            current = assert_public_url(current)
            response = client.get(
                current,
                allow_redirects=False,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.5",
                },
                timeout=timeout,
                stream=True,
            )
        except (requests.RequestException, UnsafeUrlError) as exc:
            return FetchResult(requested, None, None, {}, "", str(exc))

        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            response.close()
            if not location:
                return FetchResult(requested, current, response.status_code, {}, "", "重定向缺少 Location")
            current = urljoin(current, location)
            continue

        content = bytearray()
        try:
            for chunk in response.iter_content(chunk_size=65_536):
                if not chunk:
                    continue
                content.extend(chunk)
                if len(content) > max_bytes:
                    response.close()
                    return FetchResult(
                        requested,
                        current,
                        response.status_code,
                        {k.lower(): v for k, v in response.headers.items()},
                        "",
                        f"响应体超过 {max_bytes} 字节限制",
                    )
        except requests.RequestException as exc:
            return FetchResult(requested, current, response.status_code, {}, "", str(exc))

        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        text = content.decode(response.encoding, errors="replace")
        return FetchResult(
            requested,
            current,
            response.status_code,
            {k.lower(): v for k, v in response.headers.items()},
            text,
            None,
        )
    return FetchResult(requested, None, None, {}, "", "重定向次数超过限制")
