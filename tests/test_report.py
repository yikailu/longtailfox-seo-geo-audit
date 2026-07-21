from datetime import datetime, timezone

from longtailfox_audit.models import AuditResult, CheckResult
from longtailfox_audit.report import render_html, report_basename, write_json


def test_report_is_chinese_branded_and_self_contained(tmp_path) -> None:
    item = CheckResult(
        check_id="seo.test",
        name="测试检查",
        dimension="seo",
        section="测试",
        status="pass",
        weight=1,
        evidence=["已验证"],
        impact="测试影响",
        recommendation=None,
        url="https://example.com/",
    )
    result = AuditResult(
        schema_version="1.0.0",
        engine_version="0.1.0",
        rubric_version="1.0.0",
        generated_at=datetime.now(timezone.utc).isoformat(),
        requested_url="https://example.com/",
        final_url="https://example.com/",
        seo_score=100,
        geo_score=100,
        evidence_coverage=100,
        checks=[item],
        audited_pages=[],
        sitemap_inventory=[],
        limitations=["测试限制"],
        errors=[],
    )
    html = render_html(result, tmp_path / "report.html")
    json_file = write_json(result, tmp_path / "result.json")
    content = html.read_text(encoding="utf-8")
    assert "长尾狐" in content
    assert "data:image/png;base64," in content
    assert "@media print" in content
    assert "测试检查" in content
    assert 'data-label="检查项"' in content
    assert "min-width: 760px" not in content
    assert json_file.exists()


def test_report_basename_is_ascii_and_stable() -> None:
    result = AuditResult(
        schema_version="1.0.0",
        engine_version="0.1.0",
        rubric_version="1.0.0",
        generated_at="2026-07-21T14:30:45+08:00",
        requested_url="https://例子.测试/",
        final_url="https://例子.测试/",
        seo_score=100,
        geo_score=100,
        evidence_coverage=100,
        checks=[],
        audited_pages=[],
        sitemap_inventory=[],
        limitations=[],
        errors=[],
    )

    name = report_basename(result)

    assert name == (
        "longtailfox-seo-geo-audit-xn--fsqu00a-xn--0zwm56d-20260721-063045Z"
    )
    assert name.isascii()
