import pytest

from longtailfox_audit.security import UnsafeUrlError, normalize_url


def test_normalize_adds_https() -> None:
    assert normalize_url("example.com/path") == "https://example.com/path"


def test_normalize_preserves_public_ipv6_brackets() -> None:
    assert normalize_url("https://[2606:4700:4700::1111]/") == "https://[2606:4700:4700::1111]/"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://localhost/",
        "http://127.0.0.1/",
        "http://user:pass@example.com/",
        "https://example.com:8443/",
    ],
)
def test_rejects_unsafe_shapes(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        normalize_url(url)
