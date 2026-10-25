import os, glob, json, re, pandas as pd

account_to_user = {}
account_to_email = {}

# 1. SQL files
for p in glob.glob("dataset/evidence/databases/*.sql"):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    # matches like VALUES('account_005','user_05',...,'leila.haddad@yahoo.com'...)
    for m in re.finditer(r"VALUES\s*\(\s*['\"](account_\d+)['\"]\s*,\s*['\"](user_\d+)['\"].*?['\"]([^'\"]+@[^'\"]+)['\"]", text):
        acc, uid, em = m.group(1), m.group(2), m.group(3).lower()
        account_to_user[acc] = uid
        account_to_email[acc] = em

# 2. JSON files
for p in glob.glob("dataset/evidence/records/*.json"):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        try:
            data = json.load(f)
            sexp = data.get("service_exports", {}).get("account_service", {}).get("profile_lookups", [])
            for item in sexp:
                acc = item.get("resource_id")
                prof = item.get("profile") or {}
                em = prof.get("email")
                uid = prof.get("customer_reference")
                if acc:
                    if uid: account_to_user[acc] = uid
                    if em: account_to_email[acc] = em.lower()
        except:
            pass

# 3. LOG files
for p in glob.glob("dataset/evidence/logs/*.log"):
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "account_" in line:
                acc_m = re.search(r"resource_id=(account_\d+)", line)
                em_m = re.search(r"(?:lookup_key|email)=([^\s\"]+@[^\s\"]+)", line)
                uid_m = re.search(r"(?:customer_reference|lookup_key)=(user_\d+)", line)
                if acc_m:
                    acc = acc_m.group(1)
                    if uid_m: account_to_user[acc] = uid_m.group(1)
                    if em_m: account_to_email[acc] = em_m.group(1).lower()

print(f"Mapped {len(account_to_user)} accounts to user_id, {len(account_to_email)} accounts to email.")

# Check all 32 sample cases GT accounts
df_sample_out = pd.read_csv("dataset/sample_output.csv")
matched = 0
for idx, r in df_sample_out.iterrows():
    steps = json.loads(r["steps_json"])
    gt_acc = next((s["resource_id"] for s in steps if s["system_id"] == "account_service"), None)
    if gt_acc:
        uid = account_to_user.get(gt_acc)
        em = account_to_email.get(gt_acc)
        if uid or em:
            matched += 1
            print(f"Sample {r['case_id']}: {gt_acc} -> user: {uid}, email: {em}")
        else:
            print(f"Sample {r['case_id']}: {gt_acc} -> NOT MAPPED!")
print(f"GT account mapped: {matched} / 32")
