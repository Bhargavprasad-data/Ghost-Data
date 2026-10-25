import os
import glob
import json
import re
import csv
import pandas as pd
from pypdf import PdfReader
import sys
sys.path.append(os.path.abspath("scripts"))
from test_evidence_parser import EvidenceIndex

df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_sample_out = pd.read_csv("dataset/sample_output.csv")
df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")

# Identity maps
user_to_emails = {}
email_to_user = {}

for idx, r in df_users.iterrows():
    uid = r["user_id"]
    em = str(r["email"]).strip().lower()
    email_to_user[em] = uid
    user_to_emails.setdefault(uid, set()).add(em)

for idx, r in df_audit[df_audit["field_name"] == "email"].iterrows():
    uid = r["user_id"]
    o = str(r["old_value"]).strip().lower()
    n = str(r["new_value"]).strip().lower()
    email_to_user[o] = uid
    email_to_user[n] = uid
    user_to_emails.setdefault(uid, set()).add(o)
    user_to_emails.setdefault(uid, set()).add(n)

ev_index = EvidenceIndex()

# Count total observations
all_obs = []
for fid, obs_list in ev_index.parsed_cache.items():
    all_obs.extend(obs_list)
print(f"Total structured observations indexed across all files: {len(all_obs)}")

# Test matching for sample cases
matched_cases = 0
for idx, r in df_samples.iterrows():
    cid = r["case_id"]
    req_em = str(r["email"]).strip().lower()
    uid = email_to_user.get(req_em)
    known_emails = user_to_emails.get(uid, {req_em})
    audit_at = r["audit_at"]
    
    # Filter observations <= audit_at matching uid or any known_emails
    obs_for_user = []
    for ob in all_obs:
        if ob["captured_at"] <= audit_at:
            match = False
            if ob["user_id"] and ob["user_id"] == uid:
                match = True
            elif ob["email"] and str(ob["email"]).strip().lower() in known_emails:
                match = True
            if match:
                obs_for_user.append(ob)
                
    # Get ground truth steps
    gt_row = df_sample_out[df_sample_out["case_id"] == cid].iloc[0]
    gt_steps = json.loads(gt_row["steps_json"])
    gt_resources = [f"{s['system_id']}:{s['resource_id']}:{s['operation']}:{s['evidence_id']}" for s in gt_steps]
    
    found_resources = [f"{o['system_id']}:{o['resource_id']}:{o['state']}:{o['evidence_id']}" for o in obs_for_user]
    print(f"\n--- {cid} ({uid}) | Status: {gt_row['deletion_status']} | Audit: {audit_at} ---")
    print("  Observed count:", len(obs_for_user))
    print("  Observed:", found_resources)
    print("  GT steps:", gt_resources)
