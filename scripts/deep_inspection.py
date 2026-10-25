import os
import glob
import csv
import json
import sqlite3
import pandas as pd
from pypdf import PdfReader

def run_inspection():
    print("=================== 1. DATASET CSVs DEEP INSPECTION ===================")
    csv_files = [
        "dataset/deletion_requests.csv",
        "dataset/sample_deletion_requests.csv",
        "dataset/sample_output.csv",
        "dataset/user_identities.csv",
        "dataset/user_audit_log.csv",
        "dataset/system_activity.csv",
        "dataset/deletion_rules.csv",
        "dataset/evidence_files.csv",
        "dataset/output.csv"
    ]

    for p in csv_files:
        df = pd.read_csv(p)
        print(f"--- File: {p} ---")
        print(f"Shape: {df.shape}")
        print("Dtypes:\n", df.dtypes.to_dict())
        print("Null counts:\n", df.isnull().sum().to_dict())
        for col in df.columns:
            n_unique = df[col].nunique()
            if n_unique <= 10:
                print(f"  Col '{col}' distinct ({n_unique}): {df[col].unique().tolist()}")
            else:
                print(f"  Col '{col}' distinct count: {n_unique}")
        print()

    print("=================== 2. DELETION RULES DETAIL ===================")
    df_rules = pd.read_csv("dataset/deletion_rules.csv")
    print(df_rules.to_string())
    print()

    print("=================== 3. SYSTEM ACTIVITY EVENT TYPES & SYSTEMS ===================")
    df_act = pd.read_csv("dataset/system_activity.csv")
    print("Event types:", df_act['event_type'].value_counts().to_dict())
    print("Source systems:", df_act['source_system'].value_counts().to_dict())
    print("Target systems:", df_act['target_system'].value_counts().to_dict())
    print("Reported results:", df_act['reported_result'].value_counts().to_dict())
    print()

    print("=================== 4. RESOURCE ID PREFIXES ===================")
    prefixes = set()
    for r in df_act['resource_id'].dropna():
        if '_' in str(r):
            parts = str(r).rsplit('_', 1)
            prefixes.add(parts[0])
    print("System activity resource prefixes:", sorted(list(prefixes)))

    # Also check sample_output resource prefixes
    df_sample_out = pd.read_csv("dataset/sample_output.csv")
    out_prefixes = set()
    for s in df_sample_out['steps_json']:
        steps = json.loads(s)
        for st in steps:
            r = st.get('resource_id', '')
            if '_' in str(r):
                parts = str(r).rsplit('_', 1)
                out_prefixes.add(parts[0])
    print("Sample output resource prefixes:", sorted(list(out_prefixes)))
    print()

    print("=================== 5. REPRESENTATIVE EVIDENCE FILES ===================")
    # Check databases (.sql)
    sql_files = glob.glob("dataset/evidence/databases/*.sql")
    print(f"SQL files count: {len(sql_files)}")
    if sql_files:
        sample_sql = sql_files[0]
        print(f"Inspecting sample SQL: {sample_sql}")
        with open(sample_sql, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(30)]
        print("First 30 lines of sample SQL:\n", "".join(lines[:20]))

    # Check documents (.pdf)
    pdf_files = glob.glob("dataset/evidence/documents/*.pdf")
    print(f"\nPDF files count: {len(pdf_files)}")
    for pf in pdf_files:
        reader = PdfReader(pf)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        print(f"PDF {pf}: {len(reader.pages)} pages, text length {len(text)}, sample: {repr(text[:200])}")

    # Check records (.json, .txt)
    json_files = glob.glob("dataset/evidence/records/*.json")
    print(f"\nJSON record files count: {len(json_files)}")
    if json_files:
        sample_json = json_files[0]
        print(f"Inspecting sample JSON: {sample_json}")
        with open(sample_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            print(f"  Type: List, length: {len(data)}, sample item: {data[0] if data else 'empty'}")
        elif isinstance(data, dict):
            print(f"  Type: Dict, keys: {list(data.keys())[:10]}")

    # Check logs (.log)
    log_files = glob.glob("dataset/evidence/logs/*.log")
    print(f"\nLog files count: {len(log_files)}")
    if log_files:
        sample_log = log_files[0]
        print(f"Inspecting sample log: {sample_log}")
        with open(sample_log, "r", encoding="utf-8", errors="replace") as f:
            head = [f.readline() for _ in range(10)]
        print("Sample log lines:\n", "".join(head[:5]))

    # Check images (.png)
    img_files = glob.glob("dataset/evidence/images/*.png")
    print(f"\nImage files count: {len(img_files)}")
    for imf in img_files[:5]:
        print(f"  Image file: {imf}, size: {os.path.getsize(imf)} bytes")

if __name__ == "__main__":
    run_inspection()
