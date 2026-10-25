import pandas as pd
import json

df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_out = pd.read_csv("dataset/sample_output.csv")
df = pd.merge(df_samples, df_out, on="case_id")

for idx, r in df.iterrows():
    steps = json.loads(r['steps_json'])
    acc_steps = [s for s in steps if s['system_id'] == 'account_service']
    acc_cite = acc_steps[0]['evidence_id'] if acc_steps else "NONE"
    acc_op = acc_steps[0]['operation'] if acc_steps else "NONE"
    print(f"{r['case_id']}: status={r['deletion_status']} | audit_at={r['audit_at']} | acc_op={acc_op} | cite={acc_cite}")
