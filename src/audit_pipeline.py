"""
Audit Pipeline Module
Orchestrates end-to-end deletion audit for any deletion request:
- Identity Resolution
- Intent Verification
- Temporal Evidence & Activity State Reconstruction
- Dynamic Policy Application
- Step Planning & Verification Generation
"""

import json
from typing import Dict, Any, Tuple, List, Optional
from src.identity_resolver import IdentityResolver
from src.intent_classifier import IntentClassifier
from src.evidence_indexer import EvidenceIndexer
from src.policy_engine import PolicyEngine
from src.remediation_planner import RemediationPlanner

class AuditPipeline:
    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.identity_resolver = IdentityResolver(dataset_dir)
        self.intent_classifier = IntentClassifier()
        self.evidence_indexer = EvidenceIndexer(dataset_dir)
        self.policy_engine = PolicyEngine(dataset_dir)
        self.planner = RemediationPlanner()

    def audit_request(self, request_row: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Processes a single request row:
        case_id, email, requested_at, reported_status, reported_at, audit_at, request_text
        Returns: (case_id, deletion_status, steps_json_list)
        """
        cid = str(request_row["case_id"]).strip()
        req_email = str(request_row["email"]).strip()
        req_text = str(request_row["request_text"]).strip() if "request_text" in request_row else ""
        audit_at = str(request_row["audit_at"]).strip()
        requested_at = str(request_row.get("requested_at", "")).strip()

        # Step 1: Intent Verification
        is_authorized, reason = self.intent_classifier.is_deletion_authorized(req_text)
        if not is_authorized:
            return cid, "NOT_APPLICABLE", []

        # Step 2: Identity Resolution
        profile = self.identity_resolver.resolve(req_email)
        user_id = profile["user_id"] if profile else None
        known_emails = set(profile["all_emails"]) if profile else {req_email.lower()}

        # Step 3: Temporal Evidence Retrieval <= audit_at
        observations = self.evidence_indexer.get_observations_for_subject(
            user_id=user_id,
            emails=known_emails,
            audit_at=audit_at
        )

        # Step 4: System State Reconstruction
        # Identify resources and their latest observed state
        resources_by_id: Dict[str, Dict[str, Any]] = {}
        for ob in observations:
            res_id = ob.get("resource_id")
            if not res_id or res_id.startswith("activity_"):
                continue
            # Keep the latest observation per resource
            if res_id not in resources_by_id or ob["captured_at"] > resources_by_id[res_id]["captured_at"]:
                resources_by_id[res_id] = ob

        findings = []
        remediations = []
        verifications = []

        has_incompletion = False

        # Evaluate each secondary resource against policy
        for res_id, ob in resources_by_id.items():
            sys_id = ob["system_id"]
            cat = ob.get("category", "GENERIC")
            st = ob.get("state", "PRESENT")
            pii = ob.get("pii_exposed", False)
            ev_id = ob.get("evidence_id", "")

            # Security audit records are retained (verification only)
            if sys_id == "security_service" or cat == "SECURITY_AUDIT_LOG":
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": "security_service",
                    "resource_id": res_id,
                    "operation": "VERIFY_RECORD_PRESENT",
                    "state": "PRESENT",
                    "evidence_id": ev_id
                })
                continue

            # Account service evaluated separately below
            if sys_id == "account_service":
                continue

            eval_res = self.policy_engine.evaluate_resource(sys_id, res_id, cat, st, pii)

            if not eval_res["is_compliant"]:
                has_incompletion = True
                # Add Finding
                findings.append({
                    "phase": "FINDING",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": eval_res["finding_op"],
                    "state": eval_res["finding_state"],
                    "evidence_id": ev_id
                })
                # Add Remediation
                remediations.append({
                    "phase": "REMEDIATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": eval_res["remediation_op"],
                    "state": eval_res["remediation_state"],
                    "evidence_id": ""
                })
                # Add Verification check
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": eval_res["verification_op"],
                    "state": eval_res["verification_state"],
                    "evidence_id": ""
                })
            else:
                # Resource is compliant at audit_at -> add verification check
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": eval_res["verification_op"],
                    "state": eval_res["verification_state"],
                    "evidence_id": ev_id
                })

        # Determine Primary Account resource ID and compliance
        # Check if an account_service finding exists (e.g. failover replica drift in evidence_54 or lookup 200)
        account_obs = [ob for ob in observations if ob.get("system_id") == "account_service"]
        primary_account_id = None
        account_is_present = False
        account_ev_id = ""

        # First check if any account observation is PRESENT
        for a_ob in account_obs:
            if a_ob.get("state") == "PRESENT" and a_ob.get("pii_exposed", False):
                primary_account_id = a_ob.get("resource_id")
                account_is_present = True
                account_ev_id = a_ob.get("evidence_id", "")
                break

        if not primary_account_id:
            # Check ABSENT observations
            for a_ob in account_obs:
                if a_ob.get("resource_id") and a_ob.get("resource_id").startswith("account_"):
                    primary_account_id = a_ob.get("resource_id")
                    account_ev_id = a_ob.get("evidence_id", "")
                    break

        # Fallback account ID derived from user_id if not explicitly in evidence
        if not primary_account_id and user_id:
            num = user_id.replace("user_", "")
            primary_account_id = f"account_{num}" if len(num) > 3 else f"account_{int(num):03d}"

        # If account was still present -> create finding & remediation
        if account_is_present and primary_account_id:
            has_incompletion = True
            findings.append({
                "phase": "FINDING",
                "system_id": "account_service",
                "resource_id": primary_account_id,
                "operation": "REPORT_REMAINING_RECORD",
                "state": "PRESENT",
                "evidence_id": account_ev_id
            })
            remediations.append({
                "phase": "REMEDIATION",
                "system_id": "account_service",
                "resource_id": primary_account_id,
                "operation": "DELETE_RECORD",
                "state": "ABSENT",
                "evidence_id": ""
            })

        # In all cases (COMPLETE and INCOMPLETE), primary account must be verified ABSENT
        if primary_account_id:
            # Check if verification already exists
            if not any(v["system_id"] == "account_service" and v["resource_id"] == primary_account_id for v in verifications):
                verifications.append({
                    "phase": "VERIFICATION",
                    "system_id": "account_service",
                    "resource_id": primary_account_id,
                    "operation": "VERIFY_RECORD_ABSENT",
                    "state": "ABSENT",
                    "evidence_id": account_ev_id if not has_incompletion else ""
                })

        # Overall deletion verdict
        status = "INCOMPLETE" if has_incompletion else "COMPLETE"

        # Build sorted steps JSON
        steps = self.planner.build_steps_json(status, findings, remediations, verifications)

        return cid, status, steps
