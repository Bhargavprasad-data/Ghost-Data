import pandas as pd

df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")
df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_sample_out = pd.read_csv("dataset/sample_output.csv")

print("User identities count:", len(df_users))
print("User audit log count:", len(df_audit))
print("Audit fields:", df_audit["field_name"].value_counts().to_dict())

# Build mapping from email -> user_id, current and historical
# Also mapping from phone -> user_id, email_hash -> user_id

# Case-insensitive email maps
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

# Test sample cases
print("\n=== Resolving Sample Cases ===")
found_count = 0
for idx, r in df_samples.iterrows():
    cid = r["case_id"]
    em = str(r["email"]).strip().lower()
    uid = current_email_to_user.get(em) or history_email_to_user.get(em)
    if uid:
        found_count += 1
        # get all emails, phone, hash for this user
        u_row = df_users[df_users["user_id"] == uid].iloc[0]
        # find historical emails
        hist_emails = df_audit[(df_audit["user_id"] == uid) & (df_audit["field_name"] == "email")]
        old_emails = hist_emails["old_value"].tolist()
        print(f"Case {cid}: email '{r['email']}' -> user {uid} (Current: {u_row['email']}, Old: {old_emails})")
    else:
        print(f"Case {cid}: email '{r['email']}' -> NOT FOUND!")

print(f"\nResolved {found_count} / {len(df_samples)} sample cases.")
