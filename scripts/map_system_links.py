import csv
import json
import os
import glob
import pandas as pd

# 1. Load CSVs
df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")
df_act = pd.read_csv("dataset/system_activity.csv")
df_manifest = pd.read_csv("dataset/evidence_files.csv")
df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_sample_out = pd.read_csv("dataset/sample_output.csv")

print("=== MAPPING ID LINKS ===")

# Check how resource_id in system_activity links to user_id or emails
# Look at details column in system_activity
sample_details = df_act["details"].dropna().sample(10, random_state=42).tolist()
print("\nSample system_activity details:")
for d in sample_details:
    print(" ", d)

# Check how resource_id links to users across sample cases
# In sample_output:
# case_01: account_001
# case_02: account_002
# case_03: account_7566, audit_record_2016, analytics_9406
# case_04: account_004, analytics_901
# case_05: account_005
# case_06: account_006, search_001
# case_07: account_007, support_001
# case_08: account_008, export_001
# case_09: account_3960, audit_record_4902, backup_4978
# case_10: account_010, support_002
# case_11: search_052, analytics_2034, support_864, data_flow_9522, account_4248, audit_record_9394
# case_12: analytics_9914, account_9797, audit_record_2945

# Let's inspect where these resources appear in system_activity or evidence!
sample_resources = [
    "account_001", "account_002", "account_7566", "audit_record_2016", "analytics_9406",
    "search_052", "data_flow_9522", "support_864", "account_4248", "audit_record_9394"
]

print("\nWhere do sample resources appear in system_activity?")
for res in sample_resources:
    rows = df_act[df_act["resource_id"] == res]
    if len(rows) > 0:
        print(f"  {res} in system_activity ({len(rows)} events):")
        for idx, r in rows.iterrows():
            print(f"    {r['activity_id']} | {r['event_time']} | {r['event_type']} | {r['source_system']}->{r['target_system']} | {r['reported_result']} | {r['details']}")
    else:
        print(f"  {res} NOT in system_activity")
