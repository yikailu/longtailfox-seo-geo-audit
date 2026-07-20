#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE = SKILL_ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from longtailfox_audit.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
