from __future__ import annotations

from .models import CheckResult

VERIFIED = {"pass", "warn", "fail"}
VALUE = {"pass": 1.0, "warn": 0.5, "fail": 0.0}


def dimension_score(checks: list[CheckResult], dimension: str) -> int | None:
    verified = [
        check
        for check in checks
        if check.dimension == dimension and check.status in VERIFIED and check.weight > 0
    ]
    denominator = sum(check.weight for check in verified)
    if not denominator:
        return None
    earned = sum(check.weight * VALUE[check.status] for check in verified)
    return round(earned / denominator * 100)


def evidence_coverage(checks: list[CheckResult]) -> int:
    eligible = [check for check in checks if check.status != "info" and check.weight > 0]
    denominator = sum(check.weight for check in eligible)
    if not denominator:
        return 0
    verified = sum(check.weight for check in eligible if check.status in VERIFIED)
    return round(verified / denominator * 100)
