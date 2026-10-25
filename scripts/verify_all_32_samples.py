import json
import pandas as pd

df_sample_out = pd.read_csv("dataset/sample_output.csv")
df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_merged = pd.merge(df_samples, df_sample_out, on="case_id")

for idx, r in df_merged.iterrows():
    steps = json.loads(r["steps_json"])
    print(f"[{r['case_id']}] Status: {r['deletion_status']} | Reported: {r['reported_status']} | Audit: {r['audit_at']}")
    print(f"  Email: {r['email']}")
    for s in steps:
        print(f"    Step {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | cite: '{s['evidence_id']}'")
