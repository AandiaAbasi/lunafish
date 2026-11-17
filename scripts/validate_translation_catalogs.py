"""Fail builds when any application gettext binary catalog is invalid.

Run: python scripts/validate_translation_catalogs.py
"""
from gettext import GNUTranslations
import struct
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
broken = []
checked = 0
for path in sorted(root.rglob("*.mo")):
    # Ignore virtual environments and third-party vendored files.
    if any(part in {".venv", "venv", "node_modules", ".git"} for part in path.parts):
        continue
    checked += 1
    try:
        with path.open("rb") as catalog:
            GNUTranslations(catalog)
    except (OSError, UnicodeError, ValueError, OverflowError, struct.error) as exc:
        broken.append((path.relative_to(root), exc))

for path, exc in broken:
    print(f"BROKEN gettext catalog: {path}: {exc}", file=sys.stderr)
if broken:
    raise SystemExit(f"Translation validation failed: {len(broken)} invalid .mo file(s)")
print(f"Translation validation passed: {checked} .mo file(s)")
