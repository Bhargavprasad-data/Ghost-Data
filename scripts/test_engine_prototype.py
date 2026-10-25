import os
import glob
import json
import re
import csv
import pandas as pd
from pypdf import PdfReader

# Load reference datasets
df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
df_sample_out = pd.read_csv("dataset/sample_output.csv")
df_users = pd.read_csv("dataset/user_identities.csv")
df_audit = pd.read_csv("dataset/user_audit_log.csv")
df_rules = pd.read_csv("dataset/deletion_rules.csv")
df_manifest = pd.read_csv("dataset/evidence_files.csv")
df_act = pd.read_csv("dataset/system_activity.csv")

print("Building evidence index...")

# Build manifest lookup
manifest = []
for idx, r in df_manifest.iterrows():
    fpath = os.path.normpath(os.path.join("dataset", r["file_path"].replace("/", os.sep)))
    manifest.append({
        "file_id": r["file_id"],
        "file_path": fpath,
        "origin": r["origin"],
        "captured_at": r["captured_at"]
    })

# Sort manifest by captured_at
manifest.sort(key=lambda x: x["captured_at"])

print(f"Manifest sorted: {len(manifest)} files.")
