from typing import Any

from longtailfox_audit import pagespeed


class Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "lighthouseResult": {
                "categories": {
                    "performance": {"score": 0.91},
                    "accessibility": {"score": 0.88},
                    "best-practices": {"score": 0.95},
                    "seo": {"score": 1},
                }
            }
        }


def test_pagespeed_sends_key_in_header(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> Response:
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(pagespeed.requests, "get", fake_get)
    result = pagespeed.pagespeed_check("https://example.com/", "secret-key")

    assert result.status == "pass"
    assert captured["url"] == (
        "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
    )
    assert captured["headers"] == {"x-goog-api-key": "secret-key"}
    assert "key" not in captured["params"]
    assert captured["params"]["strategy"] == "mobile"
