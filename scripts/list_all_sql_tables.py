import glob
import re

tables = set()
for p in glob.glob("dataset/evidence/databases/*.sql"):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    for m in re.finditer(r"CREATE TABLE\s+([\"a-zA-Z0-9_]+)", text, re.IGNORECASE):
        tables.add(m.group(1).strip("\"'"))

print("All SQL tables across 24 files:")
for t in sorted(list(tables)):
    print(" ", t)
