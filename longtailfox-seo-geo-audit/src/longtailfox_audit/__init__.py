"""Longtail Fox SEO/GEO audit engine."""

__version__ = "0.1.0"

from .audit import run_audit
from .models import AuditResult, CheckResult

__all__ = ["AuditResult", "CheckResult", "run_audit", "__version__"]
