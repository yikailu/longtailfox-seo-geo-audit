from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["pass", "warn", "fail", "info", "unverified", "error"]
Dimension = Literal["seo", "geo"]


@dataclass(slots=True)
class CheckResult:
    check_id: str
    name: str
    dimension: Dimension
    section: str
    status: Status
    weight: float
    evidence: list[str]
    impact: str
    recommendation: str | None
    source: str = "deterministic"
    confidence: str = "high"
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PageSummary:
    url: str
    final_url: str
    status_code: int | None
    page_type: str
    language: str | None
    title: str | None
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["checks"] = [check.to_dict() for check in self.checks]
        return data


@dataclass(slots=True)
class AuditResult:
    schema_version: str
    engine_version: str
    rubric_version: str
    generated_at: str
    requested_url: str
    final_url: str | None
    seo_score: int | None
    geo_score: int | None
    evidence_coverage: int
    checks: list[CheckResult]
    audited_pages: list[PageSummary]
    sitemap_inventory: list[dict[str, Any]]
    limitations: list[str]
    errors: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_version": self.engine_version,
            "rubric_version": self.rubric_version,
            "generated_at": self.generated_at,
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "seo_score": self.seo_score,
            "geo_score": self.geo_score,
            "evidence_coverage": self.evidence_coverage,
            "checks": [check.to_dict() for check in self.checks],
            "audited_pages": [page.to_dict() for page in self.audited_pages],
            "sitemap_inventory": self.sitemap_inventory,
            "limitations": self.limitations,
            "errors": self.errors,
            "metadata": self.metadata,
        }
