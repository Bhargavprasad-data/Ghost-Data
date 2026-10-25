"""
Policy Engine Module
Applies deletion_rules.csv dynamically across discovered resources and states.
Maps categories and resource conditions to required treatments:
DELETE, REDACT, ANONYMIZE, DISABLE, BLOCK, or RETAIN.
"""

import os
import pandas as pd
from typing import Dict, Any, Optional

class PolicyEngine:
    def __init__(self, dataset_dir: str = "dataset"):
        self.rules_path = os.path.join(dataset_dir, "deletion_rules.csv")
        self.df_rules = pd.read_csv(self.rules_path)
        self.rules_by_category: Dict[str, Dict[str, str]] = {}
        
        for idx, r in self.df_rules.iterrows():
            cat = str(r["data_category"]).strip()
            self.rules_by_category[cat] = {
                "rule_id": str(r["rule_id"]).strip(),
                "data_category": cat,
                "condition": str(r["condition"]).strip(),
                "required_action": str(r["required_action"]).strip()
            }

    def evaluate_resource(
        self,
        system_id: str,
        resource_id: str,
        category: str,
        current_state: str,
        pii_exposed: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates a resource against policy rules and returns:
        - is_compliant: bool
        - required_action: DELETE, REDACT, ANONYMIZE, DISABLE, BLOCK, RETAIN
        - finding_op, finding_state
        - remediation_op, remediation_state
        - verification_op, verification_state
        """
        # Determine rule action
        rule = self.rules_by_category.get(category)
        action = rule["required_action"] if rule else "DELETE"
        
        # Defaults based on action
        if action == "DELETE":
            # Must be ABSENT
            is_compliant = (current_state == "ABSENT")
            return {
                "is_compliant": is_compliant,
                "action": "DELETE",
                "finding_op": "REPORT_REMAINING_RECORD",
                "finding_state": "PRESENT",
                "remediation_op": "DELETE_RECORD",
                "remediation_state": "ABSENT",
                "verification_op": "VERIFY_RECORD_ABSENT",
                "verification_state": "ABSENT"
            }
            
        elif action == "REDACT":
            # Must be REDACTED (or ABSENT)
            is_compliant = (current_state in ["REDACTED", "ABSENT"] and not pii_exposed)
            return {
                "is_compliant": is_compliant,
                "action": "REDACT",
                "finding_op": "REPORT_EXPOSED_PII",
                "finding_state": "PRESENT",
                "remediation_op": "REDACT_RECORD",
                "remediation_state": "REDACTED",
                "verification_op": "VERIFY_RECORD_REDACTED",
                "verification_state": "REDACTED"
            }
            
        elif action == "ANONYMIZE":
            # Must be ANONYMIZED
            is_compliant = (current_state in ["ANONYMIZED", "ABSENT"] and not pii_exposed)
            return {
                "is_compliant": is_compliant,
                "action": "ANONYMIZE",
                "finding_op": "REPORT_EXPOSED_PII",
                "finding_state": "PRESENT",
                "remediation_op": "ANONYMIZE_RECORD",
                "remediation_state": "ANONYMIZED",
                "verification_op": "VERIFY_RECORD_ANONYMIZED",
                "verification_state": "ANONYMIZED"
            }
            
        elif action == "DISABLE":
            # Must be DISABLED
            is_compliant = (current_state in ["DISABLED", "STOPPED"])
            return {
                "is_compliant": is_compliant,
                "action": "DISABLE",
                "finding_op": "REPORT_ACTIVE_DATA_FLOW",
                "finding_state": "ACTIVE",
                "remediation_op": "DISABLE_DATA_FLOW",
                "remediation_state": "DISABLED",
                "verification_op": "VERIFY_DATA_FLOW_DISABLED",
                "verification_state": "DISABLED"
            }
            
        elif action == "RETAIN":
            if category == "BACKUP_ARCHIVE":
                # Restore must be BLOCKED
                is_compliant = (current_state == "BLOCKED")
                return {
                    "is_compliant": is_compliant,
                    "action": "BLOCK_RESTORE",
                    "finding_op": "REPORT_RESTORE_RISK",
                    "finding_state": "ACTIVE",
                    "remediation_op": "BLOCK_RESTORE",
                    "remediation_state": "BLOCKED",
                    "verification_op": "VERIFY_RESTORE_BLOCKED",
                    "verification_state": "BLOCKED"
                }
            else:
                # Security audit log / legal hold: must be PRESENT
                is_compliant = True
                return {
                    "is_compliant": True,
                    "action": "RETAIN",
                    "finding_op": None,
                    "finding_state": None,
                    "remediation_op": None,
                    "remediation_state": None,
                    "verification_op": "VERIFY_RECORD_PRESENT",
                    "verification_state": "PRESENT"
                }

        # Fallback
        return {
            "is_compliant": (current_state == "ABSENT"),
            "action": "DELETE",
            "finding_op": "REPORT_REMAINING_RECORD",
            "finding_state": "PRESENT",
            "remediation_op": "DELETE_RECORD",
            "remediation_state": "ABSENT",
            "verification_op": "VERIFY_RECORD_ABSENT",
            "verification_state": "ABSENT"
        }
