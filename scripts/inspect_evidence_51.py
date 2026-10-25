import json

with open("dataset/evidence/records/customer_data_snapshot_bundle_20260915.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for idx, s in enumerate(data.get("snapshots", [])):
    print(f"Snapshot {idx}: system={s.get('system_id')}, category={s.get('data_category')}, records_count={len(s.get('records', []))}")
    if s.get('records'):
        print(f"  Sample record: {s['records'][0]}")
