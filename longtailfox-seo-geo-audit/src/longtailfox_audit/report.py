from __future__ import annotations

import base64
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import AuditResult, CheckResult

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
ASSET_DIR = PACKAGE_DIR / "assets"

STATUS_LABELS = {
    "pass": "通过",
    "warn": "警告",
    "fail": "失败",
    "info": "信息",
    "unverified": "未验证",
    "error": "执行错误",
}


def _logo_data_uri() -> str:
    logo = ASSET_DIR / "longtailfox-lockup.png"
    encoded = base64.b64encode(logo.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def report_basename(result: AuditResult) -> str:
    """Return one portable ASCII basename for JSON, HTML, and PDF artifacts."""
    url = result.final_url or result.requested_url
    host = urlsplit(url).hostname or "website"
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        host = "website"
    safe_host = re.sub(r"[^a-z0-9-]+", "-", host.lower()).strip("-") or "website"
    try:
        generated_at = datetime.fromisoformat(result.generated_at.replace("Z", "+00:00"))
    except ValueError:
        generated_at = datetime.now(timezone.utc)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    timestamp = generated_at.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    return f"longtailfox-seo-geo-audit-{safe_host}-{timestamp}"


def _priority(checks: list[CheckResult]) -> list[CheckResult]:
    rank = {"fail": 0, "error": 1, "warn": 2, "unverified": 3}
    actionable = [
        check
        for check in checks
        if check.status in rank and check.recommendation
    ]
    actionable.sort(key=lambda check: (rank[check.status], -check.weight, check.name))
    unique: list[CheckResult] = []
    seen: set[tuple[str, str | None]] = set()
    for check in actionable:
        key = (check.check_id, check.url)
        if key not in seen:
            unique.append(check)
            seen.add(key)
        if len(unique) >= 8:
            break
    return unique


def render_html(result: AuditResult, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("report.html")
    grouped: dict[str, list[CheckResult]] = defaultdict(list)
    for check in result.checks:
        grouped[check.section].append(check)
    counts = Counter(check.status for check in result.checks)
    domain = urlsplit(result.final_url or result.requested_url).netloc
    html = template.render(
        result=result,
        domain=domain,
        grouped=grouped,
        counts=counts,
        status_labels=STATUS_LABELS,
        priorities=_priority(result.checks),
        logo_data_uri=_logo_data_uri(),
    )
    output.write_text(html, encoding="utf-8")
    return output


def write_json(result: AuditResult, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output
