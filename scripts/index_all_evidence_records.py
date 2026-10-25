import os
import glob
import json
import sqlite3
import re
import pandas as pd
from pypdf import PdfReader

df_manifest = pd.read_csv("dataset/evidence_files.csv")
manifest_map = {}
for idx, r in df_manifest.iterrows():
    fpath = os.path.normpath(os.path.join("dataset", r["file_path"].replace("/", os.sep)))
    manifest_map[fpath] = (r["file_id"], r["origin"], r["captured_at"])

print(f"Manifest has {len(manifest_map)} files.")

# Let's inspect all evidence files by parsing them and seeing what records we extract!
def parse_all():
    file_records = {} # file_id -> list of records
    
    for fpath, (fid, origin, captured_at) in manifest_map.items():
        if not os.path.exists(fpath):
            print(f"WARNING: {fpath} does not exist!")
            continue
        ext = os.path.splitext(fpath)[1].lower()
        records = []
        
        # 1. JSON files
        if ext == ".json":
            with open(fpath, "r", encoding="utf-8") as fp:
                try:
                    data = json.load(fp)
                    records.append({"type": "json", "data": data})
                except Exception as e:
                    print(f"Error parsing JSON {fpath}: {e}")
                    
        # 2. TXT files
        elif ext == ".txt":
            with open(fpath, "r", encoding="utf-8") as fp:
                content = fp.read()
                records.append({"type": "txt", "content": content})
                
        # 3. PDF files
        elif ext == ".pdf":
            reader = PdfReader(fpath)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
            records.append({"type": "pdf", "text": text})
            
        # 4. LOG files
        elif ext == ".log":
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                lines = [line.strip() for line in fp if line.strip()]
                records.append({"type": "log", "line_count": len(lines), "sample": lines[:3]})
                
        # 5. SQL files
        elif ext == ".sql":
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
                inserts = [line for line in content.splitlines() if "INSERT INTO" in line]
                records.append({"type": "sql", "insert_count": len(inserts)})
                
        # 6. PNG files
        elif ext == ".png":
            records.append({"type": "png", "size": os.path.getsize(fpath)})

        file_records[fid] = records

    print(f"Parsed {len(file_records)} evidence files.")
    return file_records

if __name__ == "__main__":
    parse_all()
