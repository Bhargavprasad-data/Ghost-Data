import pandas as pd

df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")
df_req = pd.read_csv("dataset/deletion_requests.csv")

current_email_to_user = {}
for idx, r in df_users.iterrows():
    email = str(r["email"]).strip().lower()
    current_email_to_user[email] = r["user_id"]

history_email_to_user = {}
for idx, r in df_audit[df_audit["field_name"] == "email"].iterrows():
    old_em = str(r["old_value"]).strip().lower()
    new_em = str(r["new_value"]).strip().lower()
    history_email_to_user[old_em] = r["user_id"]
    history_email_to_user[new_em] = r["user_id"]

found_count = 0
not_found = []
for idx, r in df_req.iterrows():
    em = str(r["email"]).strip().lower()
    uid = current_email_to_user.get(em) or history_email_to_user.get(em)
    if uid:
        found_count += 1
    else:
        not_found.append((r["case_id"], r["email"]))

print(f"Resolved {found_count} / {len(df_req)} evaluation requests.")
if not_found:
    print(f"Not found ({len(not_found)}):", not_found[:10])
