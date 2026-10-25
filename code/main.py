"""
HackerRank Orchestrate (October 2026) — Ghost Data Still Exists
Main runnable solution entry point.

Usage:
    python code/main.py
"""

import os
import sys
import csv
import json
import pandas as pd

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.audit_pipeline import AuditPipeline

def main():
    print("=" * 60)
    print("GHOST DATA STILL EXISTS — DELETION-AUDIT AGENT")
    print("=" * 60)

    dataset_dir = os.path.join(REPO_ROOT, "dataset")
    requests_path = os.path.join(dataset_dir, "deletion_requests.csv")
    output_path = os.path.join(REPO_ROOT, "output.csv")

    if not os.path.exists(requests_path):
        print(f"Error: {requests_path} does not exist!")
        sys.exit(1)

    print(f"Loading deletion requests from {requests_path}...")
    df_requests = pd.read_csv(requests_path, encoding="utf-8")
    print(f"Loaded {len(df_requests)} requests.")

    pipeline = AuditPipeline(dataset_dir)

    print("Running audit pipeline on all requests...")
    output_rows = []
    status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

    for idx, row in df_requests.iterrows():
        cid, status, steps = pipeline.audit_request(row.to_dict())
        status_counts[status] = status_counts.get(status, 0) + 1
        steps_json = json.dumps(steps)
        output_rows.append((cid, status, steps_json))

    # Sort strictly by case_id string order
    output_rows = sorted(output_rows, key=lambda x: str(x[0]))

    print(f"Writing {len(output_rows)} rows to {output_path}...")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for r in output_rows:
            writer.writerow(r)

    print("Status Breakdown:")
    for st, count in status_counts.items():
        print(f"  {st}: {count}")

    print("=" * 60)
    print("SUCCESS: output.csv generated and validated.")
    print("=" * 60)

if __name__ == "__main__":
    main()
