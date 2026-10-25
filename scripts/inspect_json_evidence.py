import json

with open("dataset/evidence/records/service_resource_export_20260915_114455.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys:", data.keys() if isinstance(data, dict) else f"List of {len(data)}")
if isinstance(data, dict):
    for k in data.keys():
        val = data[k]
        if isinstance(val, list):
            print(f"Key '{k}': list of {len(val)} items. Sample item: {val[0] if val else 'empty'}")
        else:
            print(f"Key '{k}': {val}")
