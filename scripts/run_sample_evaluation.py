import os
import sys
import pandas as pd

sys.path.append(os.path.abspath("."))

from src.audit_pipeline import AuditPipeline
from src.evaluator import Evaluator

df_samples = pd.read_csv("dataset/sample_deletion_requests.csv")
pipeline = AuditPipeline("dataset")
evaluator = Evaluator("dataset/sample_output.csv")

print(f"Running evaluation on {len(df_samples)} sample cases...")
predictions = []
for idx, r in df_samples.iterrows():
    cid, status, steps = pipeline.audit_request(r.to_dict())
    predictions.append((cid, status, steps))

res = evaluator.evaluate(predictions)
print(f"\n================ EVALUATION RESULTS ================")
print(f"Total Cases: {res['total_cases']}")
print(f"Status Accuracy: {res['status_accuracy']*100:.2f}% ({res['status_matches']}/{res['total_cases']})")
print(f"Sequence Accuracy: {res['sequence_accuracy']*100:.2f}% ({res['sequence_matches']}/{res['total_cases']})")
print(f"Field Accuracy: {res['field_accuracy']*100:.2f}%")
print(f"Mismatches: {len(res['mismatches'])}")

if res["mismatches"]:
    print("\n--- FIRST 5 MISMATCHES ---")
    for m in res["mismatches"][:5]:
        print(f"\nCase {m['case_id']}: Pred Status={m['pred_status']} vs GT={m['gt_status']}")
        p_strs = [f"{s['system_id']}:{s['resource_id']}:{s['operation']}:{s.get('evidence_id', '')}" for s in m['pred_steps']]
        g_strs = [f"{s['system_id']}:{s['resource_id']}:{s['operation']}:{s.get('evidence_id', '')}" for s in m['gt_steps']]
        print(f"  Pred Steps ({m['pred_steps_count']}): {p_strs}")
        print(f"  GT Steps ({m['gt_steps_count']}): {g_strs}")
