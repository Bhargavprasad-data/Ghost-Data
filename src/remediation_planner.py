"""
Remediation Planner Module
Constructs and sorts ordered steps_json following the exact challenge specification:
- Phase ordering: FINDING -> REMEDIATION -> VERIFICATION
- Operation priority tables per phase
- Tie-breaking: system_id ascending, resource_id ascending
- Evidence citation rules:
    - COMPLETE: verification steps cite real evidence IDs
    - INCOMPLETE: findings cite evidence IDs, remediation & verification use ""
- Consecutive step_no starting at 1
"""

from typing import List, Dict, Any

FINDING_OPS = [
    "REPORT_REMAINING_RECORD",
    "REPORT_EXPOSED_PII",
    "REPORT_ACTIVE_DATA_FLOW",
    "REPORT_RESTORE_RISK"
]

REMEDIATION_OPS = [
    "DISABLE_DATA_FLOW",
    "BLOCK_RESTORE",
    "DELETE_RECORD",
    "REDACT_RECORD",
    "ANONYMIZE_RECORD"
]

VERIFICATION_OPS = [
    "VERIFY_RECORD_ABSENT",
    "VERIFY_RECORD_PRESENT",
    "VERIFY_RECORD_REDACTED",
    "VERIFY_RECORD_ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED",
    "VERIFY_RESTORE_BLOCKED"
]

class RemediationPlanner:
    def __init__(self):
        self.finding_op_rank = {op: i for i, op in enumerate(FINDING_OPS)}
        self.remediation_op_rank = {op: i for i, op in enumerate(REMEDIATION_OPS)}
        self.verification_op_rank = {op: i for i, op in enumerate(VERIFICATION_OPS)}

    def build_steps_json(
        self,
        deletion_status: str,
        findings: List[Dict[str, Any]],
        remediations: List[Dict[str, Any]],
        verifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Takes raw step dictionaries and outputs sorted, numbered steps array.
        """
        if deletion_status == "NOT_APPLICABLE":
            return []

        # 1. Sort findings
        sorted_findings = sorted(
            findings,
            key=lambda s: (
                self.finding_op_rank.get(s["operation"], 99),
                s["system_id"],
                s["resource_id"]
            )
        )

        # 2. Sort remediations
        sorted_remediations = sorted(
            remediations,
            key=lambda s: (
                self.remediation_op_rank.get(s["operation"], 99),
                s["system_id"],
                s["resource_id"]
            )
        )

        # 3. Sort verifications
        sorted_verifications = sorted(
            verifications,
            key=lambda s: (
                self.verification_op_rank.get(s["operation"], 99),
                s["system_id"],
                s["resource_id"]
            )
        )

        # Combine phases
        all_steps = []
        if deletion_status == "COMPLETE":
            # COMPLETE contains ONLY verification steps
            all_steps.extend(sorted_verifications)
        else:
            # INCOMPLETE contains FINDING -> REMEDIATION -> VERIFICATION
            all_steps.extend(sorted_findings)
            all_steps.extend(sorted_remediations)
            all_steps.extend(sorted_verifications)

        # Assign consecutive 1-based step numbers and enforce citation rules
        result = []
        for idx, step in enumerate(all_steps, start=1):
            phase = step["phase"]
            ev_id = step.get("evidence_id", "")
            
            # Evidence citation rule:
            # INCOMPLETE remediation and verification must use empty string ""
            if deletion_status == "INCOMPLETE" and phase in ["REMEDIATION", "VERIFICATION"]:
                ev_id = ""
                
            formatted = {
                "step_no": idx,
                "phase": phase,
                "system_id": step["system_id"],
                "resource_id": step["resource_id"],
                "operation": step["operation"],
                "state": step["state"],
                "evidence_id": ev_id
            }
            result.append(formatted)

        return result
