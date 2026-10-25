import os

targets = ["account_3960", "audit_record_4902"]
for root, dirs, files in os.walk("dataset"):
    for f in files:
        p = os.path.join(root, f)
        if f.endswith((".csv", ".json", ".log", ".sql", ".txt")):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    for t in targets:
                        if t in content:
                            print(f"Found {t} in {p}")
            except Exception:
                pass
