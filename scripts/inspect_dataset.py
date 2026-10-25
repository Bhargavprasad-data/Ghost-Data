import os
import glob
import csv
import json

def inspect_csvs():
    print("=================== CSV INVENTORY ===================")
    for p in sorted(glob.glob("dataset/*.csv")):
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            rows = list(reader)
        print(f"File: {p}")
        print(f"  Rows: {len(rows)} | Cols: {len(header) if header else 0}")
        print(f"  Header: {header}")
        if rows:
            print(f"  Sample row 1: {rows[0]}")
            if len(rows) > 1:
                print(f"  Sample row 2: {rows[1]}")
        print()

def inspect_evidence():
    print("=================== EVIDENCE INVENTORY ===================")
    for root, dirs, files in os.walk("dataset/evidence"):
        if files:
            exts = {}
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                exts[ext] = exts.get(ext, 0) + 1
            print(f"{root}: {len(files)} files, types: {exts}")

if __name__ == "__main__":
    inspect_csvs()
    inspect_evidence()
