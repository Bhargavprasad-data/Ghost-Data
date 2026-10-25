import os
import glob
import json
import pandas as pd

df_sample_out = pd.read_csv("dataset/sample_output.csv")

all_sample_resources = {} # res_id -> list of (case_id, step)
for idx, r in df_sample_out.iterrows():
    cid = r["case_id"]
    steps = json.loads(r["steps_json"])
    for s in steps:
        res = s["resource_id"]
        all_sample_resources.setdefault(res, []).append((cid, s))

print(f"Total unique sample resources: {len(all_sample_resources)}")

# Search across all files in dataset/
res_sources = {}
for root, dirs, files in os.walk("dataset"):
    if "sample_output" in root: continue
    for f in files:
        if f in ["sample_output.csv"]: continue
        p = os.path.join(root, f)
        ext = os.path.splitext(f)[1].lower()
        if ext in [".csv", ".json", ".log", ".sql", ".txt", ".pdf"]:
            try:
                if ext == ".pdf":
                    from pypdf import PdfReader
                    content = "\n".join([page.extract_text() or "" for page in PdfReader(p).pages])
                else:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                
                for res in all_sample_resources.keys():
                    if res in content:
                        res_sources.setdefault(res, []).append(p)
            except Exception as e:
                pass

print("\nResource source mapping summary:")
found_count = 0
for res, cases in all_sample_resources.items():
    srcs = res_sources.get(res, [])
    if srcs:
        found_count += 1
        print(f"  {res} ({cases[0][0]}) -> found in {len(srcs)} files: {[os.path.basename(s) for s in srcs[:3]]}")
    else:
        print(f"  {res} ({cases[0][0]}) -> NOT FOUND!")

print(f"\nTotal found: {found_count} / {len(all_sample_resources)}")
