import csv
import pandas as pd

df_req = pd.read_csv("dataset/deletion_requests.csv")
print(f"Total requests: {len(df_req)}")
print("Cases min and max:", df_req["case_id"].min(), df_req["case_id"].max())

non_del_cases = ["case_533", "case_535", "case_540", "case_541"]
for cid in non_del_cases:
    rows = df_req[df_req["case_id"] == cid]
    if len(rows) > 0:
        r = rows.iloc[0]
        print(f"\n--- {cid} ---")
        print("Email:", r["email"])
        print("Requested at:", r["requested_at"])
        print("Reported status:", r["reported_status"])
        print("Reported at:", r["reported_at"])
        print("Audit at:", r["audit_at"])
        print("Request text:\n", r["request_text"])

# Let's inspect rows from 525 to 550
print("\n=== Sample of requests near the end (case_530..case_550) ===")
for idx, r in df_req.tail(25).iterrows():
    print(f"{r['case_id']} | {r['email']} | {r['reported_status']} | text[:70]: {r['request_text'][:70]}")
