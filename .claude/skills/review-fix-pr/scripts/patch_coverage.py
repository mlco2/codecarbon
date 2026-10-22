"""Coverage of the lines changed by a branch, as Codecov's patch check sees it.

Usage:
    git diff -U0 master...HEAD -- codecarbon/ > diff.patch
    uv run task test-coverage            # writes coverage.xml
    python -I patch_coverage.py diff.patch coverage.xml
"""

import re
import sys
import xml.etree.ElementTree as ET

added = {}
current = None
for line in open(sys.argv[1]):
    if line.startswith("+++ b/"):
        current = line[6:].strip()
        added[current] = set()
    hunk = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
    if hunk:
        start, count = int(hunk[1]), int(hunk[2] or 1)
        added[current].update(range(start, start + count))

hits = {}
for cls in ET.parse(sys.argv[2]).iter("class"):
    name = cls.get("filename")
    if not name.startswith("codecarbon/"):
        name = "codecarbon/" + name
    hits[name] = {int(x.get("number")): int(x.get("hits")) for x in cls.iter("line")}

total = covered = 0
for path, lines in sorted(added.items()):
    file_hits = hits.get(path, {})
    measured = sorted(n for n in lines if n in file_hits)
    missed = [n for n in measured if file_hits[n] == 0]
    total += len(measured)
    covered += len(measured) - len(missed)
    print(f"{path}: {len(measured) - len(missed)}/{len(measured)} missed: {missed}")
print(f"patch: {covered}/{total} ({100 * covered / max(total, 1):.1f}%)")
