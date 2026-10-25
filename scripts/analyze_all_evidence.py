import os
import glob
import json
import sqlite3
import pandas as pd
from pypdf import PdfReader

df_manifest = pd.read_csv("dataset/evidence_files.csv")
print(f"Total manifest rows: {len(df_manifest)}")

evidence_types = {}
for idx, row in df_manifest.iterrows():
    fpath = os.path.join("dataset", row["file_path"].replace("/", os.sep))
    ext = os.path.splitext(fpath)[1].lower()
    evidence_types.setdefault(ext, []).append((row["file_id"], fpath, row["origin"], row["captured_at"]))

for ext, items in evidence_types.items():
    print(f"Extension {ext}: {len(items)} files")

# Let's inspect SQL files
print("\n=== SQL EVIDENCE FILES ===")
sql_items = evidence_types.get(".sql", [])
print(f"Number of SQL files: {len(sql_items)}")
for file_id, fpath, origin, captured_at in sql_items[:5]:
    # Check tables in SQL file by reading CREATE TABLE statements
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    tables = [line for line in content.splitlines() if "CREATE TABLE" in line]
    inserts = [line for line in content.splitlines() if "INSERT INTO" in line]
    print(f"  {file_id} ({os.path.basename(fpath)}): {len(tables)} tables, {len(inserts)} inserts")
    for t in tables[:3]:
        print(f"    Table: {t[:80]}")

# Let's inspect JSON files
print("\n=== JSON EVIDENCE FILES ===")
json_items = evidence_types.get(".json", [])
print(f"Number of JSON files: {len(json_items)}")
for file_id, fpath, origin, captured_at in json_items[:8]:
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    keys = list(data.keys()) if isinstance(data, dict) else f"list({len(data)})"
    print(f"  {file_id} ({os.path.basename(fpath)}): keys={keys}")

# Let's inspect LOG files
print("\n=== LOG EVIDENCE FILES ===")
log_items = evidence_types.get(".log", [])
print(f"Number of LOG files: {len(log_items)}")
for file_id, fpath, origin, captured_at in log_items[:5]:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]
    print(f"  {file_id} ({os.path.basename(fpath)}): {len(lines)} lines. Sample line: {lines[0][:100] if lines else 'empty'}")
