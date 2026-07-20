#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    skill_file = path / "SKILL.md"
    if not skill_file.exists():
        return ["缺少 SKILL.md"]
    if not re.fullmatch(r"[a-z0-9-]{1,63}", path.name):
        errors.append("Skill 目录名必须使用小写字母、数字和连字符，且少于 64 字符")
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        return errors + ["SKILL.md 缺少有效 YAML frontmatter"]
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    keys = [line.split(":", 1)[0].strip() for line in lines if ":" in line]
    if keys != ["name", "description"]:
        errors.append("SKILL.md frontmatter 只能按顺序包含 name 和 description")
    name_line = next((line for line in lines if line.startswith("name:")), "")
    if name_line.partition(":")[2].strip() != path.name:
        errors.append("frontmatter name 必须与目录名一致")
    if not next((line for line in lines if line.startswith("description:")), ""):
        errors.append("frontmatter 缺少 description")
    for required in ("agents/openai.yaml", "scripts/run-audit.py", "assets/longtailfox-lockup.png"):
        if not (path / required).exists():
            errors.append(f"缺少必要文件：{required}")
    return errors


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "longtailfox-seo-geo-audit")
    errors = validate(target)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
