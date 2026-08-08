#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_root"

python3 - <<'PY'
from pathlib import Path
import re
import sys

root = Path.cwd()
paths = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
pattern = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
failures: list[str] = []

for source in paths:
    text = source.read_text(encoding="utf-8")
    for target in pattern.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean_target = target.split("#", 1)[0]
        if not clean_target:
            continue
        resolved = (source.parent / clean_target).resolve()
        if not resolved.exists():
            failures.append(f"{source.relative_to(root)} -> {target}")

if failures:
    print("Broken local Markdown links:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    raise SystemExit(1)

print("Local Markdown links passed.")
PY
