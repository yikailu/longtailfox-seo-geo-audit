from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


class UnsafeUrlError(ValueError):
    pass


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise UnsafeUrlError("URL 不能为空")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeUrlError("仅支持 HTTP/HTTPS URL")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("URL 不得包含用户名或密码")
    if not parsed.hostname:
        raise UnsafeUrlError("URL 缺少有效主机名")
    port = parsed.port
    if port and port not in {80, 443}:
        raise UnsafeUrlError("仅允许标准 HTTP/HTTPS 端口")
    host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise UnsafeUrlError("拒绝本地或内网主机")
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None and not literal_ip.is_global:
        raise UnsafeUrlError(f"拒绝非公网地址：{literal_ip}")
    netloc = f"[{host}]" if literal_ip is not None and literal_ip.version == 6 else host
    if port:
        netloc = f"{netloc}:{port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def assert_public_url(url: str) -> str:
    normalized = normalize_url(url)
    host = urlsplit(normalized).hostname
    if host is None:
        raise UnsafeUrlError("URL 缺少主机名")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"域名无法解析：{host}") from exc
    if not addresses:
        raise UnsafeUrlError(f"域名没有可用地址：{host}")
    for raw in addresses:
        ip = ipaddress.ip_address(raw)
        if not ip.is_global:
            raise UnsafeUrlError(f"拒绝非公网地址：{ip}")
    return normalized
