import pandas as pd
from datetime import datetime, timedelta

df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_sample_out = pd.read_csv("dataset/sample_output.csv")
df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")
df_act = pd.read_csv("dataset/system_activity.csv")

# Filter deletion worker account submissions
del_accounts = df_act[
    (df_act["source_system"] == "deletion_worker") &
    (df_act["target_system"] == "account_service") &
    (df_act["event_type"] == "DELETE_RECORD")
].copy()
del_accounts["event_time_dt"] = pd.to_datetime(del_accounts["event_time"])
del_accounts = del_accounts.sort_values("event_time_dt")

print(f"Total deletion worker account deletions: {len(del_accounts)}")

# For each sample case, find the matching account_id from sample_output
for idx, r in df_samples.iterrows():
    cid = r["case_id"]
    req_dt = pd.to_datetime(r["requested_at"])
    rep_dt = pd.to_datetime(r["reported_at"])
    aud_dt = pd.to_datetime(r["audit_at"])
    
    # GT account_id
    gt_row = df_sample_out[df_sample_out["case_id"] == cid].iloc[0]
    import json
    steps = json.loads(gt_row["steps_json"])
    gt_acc = next((s["resource_id"] for s in steps if s["system_id"] == "account_service"), None)
    
    # candidate events in [req_dt, rep_dt + 1 hour]
    candidates = del_accounts[
        (del_accounts["event_time_dt"] >= req_dt) &
        (del_accounts["event_time_dt"] <= rep_dt + timedelta(hours=1))
    ]
    print(f"{cid} (GT: {gt_acc}) | req: {r['requested_at']} | rep: {r['reported_at']}")
    print(f"  Candidates count: {len(candidates)}")
    for _, c in candidates.iterrows():
        is_match = (c["resource_id"] == gt_acc)
        print(f"    {'[MATCH]' if is_match else '       '} {c['activity_id']} | {c['event_time']} | {c['resource_id']}")
