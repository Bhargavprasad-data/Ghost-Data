import pandas as pd
from datetime import datetime, timedelta

df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")
df_act = pd.read_csv("dataset/system_activity.csv")

# Build email to user_id
current_email_to_user = {str(r["email"]).strip().lower(): r["user_id"] for idx, r in df_users.iterrows()}
for idx, r in df_audit[df_audit["field_name"] == "email"].iterrows():
    current_email_to_user[str(r["old_value"]).strip().lower()] = r["user_id"]
    current_email_to_user[str(r["new_value"]).strip().lower()] = r["user_id"]

for idx, r in df_samples.head(15).iterrows():
    cid = r["case_id"]
    em = str(r["email"]).strip().lower()
    uid = current_email_to_user.get(em)
    req_at = r["requested_at"]
    rep_at = r["reported_at"]
    aud_at = r["audit_at"]
    print(f"================ {cid} ({uid}) ================")
    print(f"Req: {req_at} | Rep: {rep_at} | Audit: {aud_at}")
    
    # Check if user_id or email appears in details or resource_id
    matches = df_act[
        df_act["details"].str.contains(em, case=False, na=False) |
        (df_act["details"].str.contains(uid, case=False, na=False) if uid else False) |
        df_act["resource_id"].str.contains(em, case=False, na=False) |
        (df_act["resource_id"].str.contains(uid, case=False, na=False) if uid else False)
    ]
    print(f"Direct text matches in system_activity: {len(matches)}")
    if len(matches) > 0:
        for _, m in matches.iterrows():
            print(f"  {m['activity_id']} | {m['event_time']} | {m['event_type']} | {m['resource_id']} | {m['reported_result']}")
            
    # Also check events between requested_at and reported_at (+/- 2 hours)
    t_start = pd.to_datetime(req_at)
    t_end = pd.to_datetime(rep_at) + timedelta(hours=2)
    df_act_time = df_act[(pd.to_datetime(df_act["event_time"]) >= t_start) & (pd.to_datetime(df_act["event_time"]) <= t_end)]
    # Deletion worker events
    del_events = df_act_time[df_act_time["source_system"] == "deletion_worker"]
    print(f"Deletion worker events in [req, rep+2h]: {len(del_events)}")
    for _, d in del_events.head(5).iterrows():
        print(f"  del_worker: {d['activity_id']} | {d['event_time']} | {d['event_type']} | {d['resource_id']} | {d['details']}")
