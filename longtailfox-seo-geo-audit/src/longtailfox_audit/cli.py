from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .audit import run_audit
from .pdf import render_pdf
from .report import render_html, write_json
from .security import UnsafeUrlError


def _slug(url: str) -> str:
    host = urlsplit(url).netloc.lower().replace(".", "-").replace(":", "-")
    return host or "website"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="生成长尾狐品牌中文 SEO/GEO 审计报告"
    )
    parser.add_argument("url", help="公开网站 URL")
    parser.add_argument("--max-pages", type=int, default=8, help="代表页面上限，1-20")
    parser.add_argument("--output-dir", default="reports", help="报告输出目录")
    parser.add_argument("--pagespeed-api-key", help="可选 PageSpeed Insights API Key")
    parser.add_argument("--no-pdf", action="store_true", help="不尝试生成 PDF")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_audit(
            args.url,
            max_pages=args.max_pages,
            pagespeed_api_key=args.pagespeed_api_key,
            progress=lambda stage, percent: print(
                f"[{percent:>3}%] {stage}", file=sys.stderr, flush=True
            ),
        )
    except (UnsafeUrlError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    name = f"{_slug(result.final_url or result.requested_url)}-seo-geo-audit"
    json_path = write_json(result, output_dir / f"{name}.json")
    html_path = render_html(result, output_dir / f"{name}.html")
    print(f"JSON: {json_path}")
    print(f"HTML: {html_path}")
    if not args.no_pdf:
        ok, detail = render_pdf(html_path, output_dir / f"{name}.pdf")
        if ok:
            print(f"PDF: {detail}")
        else:
            print(f"PDF 未生成：{detail}", file=sys.stderr)
    return 0 if result.final_url else 1


if __name__ == "__main__":
    raise SystemExit(main())
