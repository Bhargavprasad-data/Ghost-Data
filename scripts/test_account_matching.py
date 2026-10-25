import pandas as pd
from datetime import datetime

df_del = pd.read_csv("dataset/deletion_requests.csv")
df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_all_reqs = pd.concat([df_samples, df_del], ignore_index=True)
df_all_reqs["rep_dt"] = pd.to_datetime(df_all_reqs["reported_at"])
df_all_reqs["req_dt"] = pd.to_datetime(df_all_reqs["requested_at"])

df_act = pd.read_csv("dataset/system_activity.csv")
del_worker_acc = df_act[
    (df_act["source_system"] == "deletion_worker") &
    (df_act["target_system"] == "account_service") &
    (df_act["event_type"] == "DELETE_RECORD")
].copy()
del_worker_acc["event_time_dt"] = pd.to_datetime(del_worker_acc["event_time"])

print("Testing nearest event matching...")
# For each sample case 11..32, let's find the closest deletion worker event to reported_at (that is <= reported_at + 20 minutes)
df_sample_out = pd.read_csv("dataset/sample_output.csv")
import json
correct = 0
total = 0
for idx, r in df_samples.iterrows():
    cid = r["case_id"]
    if cid in ["case_01", "case_02", "case_04", "case_05", "case_06", "case_07", "case_08", "case_10"]:
        continue
    total += 1
    rep_dt = pd.to_datetime(r["reported_at"])
    req_dt = pd.to_datetime(r["requested_at"])
    
    # candidate events between req_dt and rep_dt + 1 hour
    cands = del_worker_acc[
        (del_worker_acc["event_time_dt"] >= req_dt) &
        (del_worker_acc["event_time_dt"] <= rep_dt + pd.Timedelta(hours=2))
    ].copy()
    if len(cands) > 0:
        cands["diff"] = (cands["event_time_dt"] - rep_dt).abs()
        closest = cands.sort_values("diff").iloc[0]
        chosen_acc = closest["resource_id"]
        
        gt_row = df_sample_out[df_sample_out["case_id"] == cid].iloc[0]
        steps = json.loads(gt_row["steps_json"])
        gt_acc = next((s["resource_id"] for s in steps if s["system_id"] == "account_service"), None)
        if chosen_acc == gt_acc:
            correct += 1
            print(f"{cid}: MATCH -> {chosen_acc}")
        else:
            print(f"{cid}: MISMATCH -> chosen {chosen_acc} vs GT {gt_acc} (diff: {closest['diff']})")

print(f"Accuracy: {correct} / {total}")
