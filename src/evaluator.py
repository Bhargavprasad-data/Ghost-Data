"""
Evaluator Module
Evaluates pipeline predictions against ground truth sample outputs:
- Case-level deletion_status accuracy
- Step-level presence and count accuracy
- Field-level accuracy (phase, system_id, resource_id, operation, state, evidence_id)
- Sequence accuracy (exact ordered array match)
"""

import json
import pandas as pd
from typing import Dict, Any, List, Tuple

class Evaluator:
    def __init__(self, ground_truth_path: str = "dataset/sample_output.csv"):
        self.df_gt = pd.read_csv(ground_truth_path)
        self.gt_by_case = {}
        for idx, r in self.df_gt.iterrows():
            cid = str(r["case_id"]).strip()
            status = str(r["deletion_status"]).strip()
            steps = json.loads(r["steps_json"]) if pd.notna(r["steps_json"]) else []
            self.gt_by_case[cid] = {
                "deletion_status": status,
                "steps": steps
            }

    def evaluate(self, predictions: List[Tuple[str, str, List[Dict[str, Any]]]]) -> Dict[str, Any]:
        """
        predictions: list of (case_id, deletion_status, steps_list)
        """
        total_cases = len(predictions)
        status_matches = 0
        sequence_matches = 0
        total_gt_steps = 0
        matched_steps = 0
        field_matches = 0
        field_total = 0

        mismatches = []

        for cid, pred_status, pred_steps in predictions:
            if cid not in self.gt_by_case:
                continue
            gt = self.gt_by_case[cid]
            gt_status = gt["deletion_status"]
            gt_steps = gt["steps"]
            total_gt_steps += len(gt_steps)

            # 1. Status match
            s_match = (pred_status == gt_status)
            if s_match:
                status_matches += 1

            # 2. Sequence match
            # Compare steps ignoring whitespace and key order
            seq_match = False
            if s_match and len(pred_steps) == len(gt_steps):
                all_step_eq = True
                for p_s, g_s in zip(pred_steps, gt_steps):
                    for k in ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                        field_total += 1
                        if str(p_s.get(k, "")).strip() == str(g_s.get(k, "")).strip():
                            field_matches += 1
                        else:
                            all_step_eq = False
                if all_step_eq:
                    seq_match = True
                    sequence_matches += 1
            else:
                for g_s in gt_steps:
                    field_total += 6

            if not seq_match or not s_match:
                mismatches.append({
                    "case_id": cid,
                    "pred_status": pred_status,
                    "gt_status": gt_status,
                    "pred_steps_count": len(pred_steps),
                    "gt_steps_count": len(gt_steps),
                    "pred_steps": pred_steps,
                    "gt_steps": gt_steps
                })

        return {
            "total_cases": total_cases,
            "status_accuracy": status_matches / total_cases if total_cases > 0 else 0.0,
            "sequence_accuracy": sequence_matches / total_cases if total_cases > 0 else 0.0,
            "field_accuracy": field_matches / field_total if field_total > 0 else 0.0,
            "status_matches": status_matches,
            "sequence_matches": sequence_matches,
            "mismatches": mismatches
        }
