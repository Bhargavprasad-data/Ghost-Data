import csv
import json
import sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_output = pd.read_csv("dataset/sample_output.csv")
df_merged = pd.merge(df_samples, df_output, on="case_id")

with open("scripts/sample_traces.txt", "w", encoding="utf-8") as out:
    for idx, row in df_merged.iterrows():
        steps = json.loads(row["steps_json"])
        out.write(f"==================================================\n")
        out.write(f"CASE: {row['case_id']} | Email: {row['email']} | Status: {row['deletion_status']} (Reported: {row['reported_status']})\n")
        out.write(f"Requested: {row['requested_at']} | Reported: {row['reported_at']} | Audit: {row['audit_at']}\n")
        out.write(f"Request Text:\n  {row['request_text']}\n")
        out.write(f"Steps ({len(steps)}):\n")
        for s in steps:
            out.write(f"  [{s['step_no']}] {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | cite: '{s['evidence_id']}'\n")

print("Saved sample traces to scripts/sample_traces.txt")
