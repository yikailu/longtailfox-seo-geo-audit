from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def find_browser() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def render_pdf(html_path: str | Path, pdf_path: str | Path, timeout: int = 120) -> tuple[bool, str]:
    browser = find_browser()
    if not browser:
        return False, "未找到 Chromium/Google Chrome"
    html = Path(html_path).resolve()
    pdf = Path(pdf_path).resolve()
    pdf.parent.mkdir(parents=True, exist_ok=True)
    command = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        f"--print-to-pdf={pdf}",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        html.as_uri(),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)
    if completed.returncode != 0 or not pdf.exists():
        return False, (completed.stderr or completed.stdout or "PDF 渲染失败").strip()
    return True, str(pdf)
