import csv
import json

def analyze():
    print("=== DELETION RULES ===")
    with open("dataset/deletion_rules.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(dict(row))

    print("\n=== SAMPLE OUTPUT ANALYSIS ===")
    with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
        samples = list(csv.DictReader(f))

    status_counts = {}
    for s in samples:
        status_counts[s["deletion_status"]] = status_counts.get(s["deletion_status"], 0) + 1
    print("Status counts:", status_counts)

    for s in samples:
        steps = json.loads(s["steps_json"])
        ops = [f"{st['phase']}:{st['operation']}:{st['system_id']}:{st['resource_id']}:{st['evidence_id']}" for st in steps]
        print(f"{s['case_id']}: {s['deletion_status']} ({len(steps)} steps) -> {ops}")

if __name__ == "__main__":
    analyze()
