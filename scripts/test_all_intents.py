import os
import sys
sys.path.append(os.path.abspath("."))
import pandas as pd
from src.intent_classifier import IntentClassifier

df_req = pd.read_csv("dataset/deletion_requests.csv")
classifier = IntentClassifier()

non_del = []
for idx, r in df_req.iterrows():
    cid = r["case_id"]
    text = str(r["request_text"])
    is_auth, reason = classifier.is_deletion_authorized(text)
    if not is_auth:
        non_del.append((cid, r["email"], reason, text))

print(f"Total NOT_APPLICABLE detected: {len(non_del)} / {len(df_req)}")
for cid, em, reason, txt in non_del:
    print(f"\n{cid} | {em} | {reason}\n  Text: {txt}")
