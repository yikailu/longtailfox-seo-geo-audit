from longtailfox_audit.models import CheckResult
from longtailfox_audit.scoring import dimension_score, evidence_coverage


def check(status: str, weight: float, dimension: str = "seo") -> CheckResult:
    return CheckResult(
        check_id=f"x.{status}",
        name=status,
        dimension=dimension,  # type: ignore[arg-type]
        section="test",
        status=status,  # type: ignore[arg-type]
        weight=weight,
        evidence=["e"],
        impact="i",
        recommendation=None,
    )


def test_scores_exclude_unverified() -> None:
    checks = [check("pass", 2), check("warn", 2), check("unverified", 6)]
    assert dimension_score(checks, "seo") == 75
    assert evidence_coverage(checks) == 40


def test_info_does_not_reduce_coverage() -> None:
    checks = [check("pass", 2), check("info", 100)]
    assert evidence_coverage(checks) == 100
