import json
import pandas as pd

df_ev = pd.read_csv("dataset/evidence_files.csv")
img_ids = df_ev[df_ev["file_path"].str.endswith(".png")]["file_id"].tolist()
pdf_ids = df_ev[df_ev["file_path"].str.endswith(".pdf")]["file_id"].tolist()
print("Image evidence IDs:", img_ids)
print("PDF evidence IDs:", pdf_ids)

df_sample_out = pd.read_csv("dataset/sample_output.csv")
for idx, r in df_sample_out.iterrows():
    steps = json.loads(r["steps_json"])
    for s in steps:
        if s.get("evidence_id") in img_ids:
            print(f"Sample {r['case_id']} cited image: {s['evidence_id']}")
        if s.get("evidence_id") in pdf_ids:
            print(f"Sample {r['case_id']} cited PDF: {s['evidence_id']}")
