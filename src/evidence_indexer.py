"""
Evidence Indexer Module
Parses and indexes all 94 evidence files under dataset/evidence/ along with system_activity.csv.
Provides point-in-time retrieval of resource observations for any subject profile up to audit_at.
"""

import os
import re
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Set
from pypdf import PdfReader

class EvidenceIndexer:
    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.manifest_path = os.path.join(dataset_dir, "evidence_files.csv")
        self.activity_path = os.path.join(dataset_dir, "system_activity.csv")
        
        self.df_manifest = pd.read_csv(self.manifest_path)
        self.df_activity = pd.read_csv(self.activity_path)
        
        self.manifest = []
        for idx, r in self.df_manifest.iterrows():
            fpath = os.path.normpath(os.path.join(dataset_dir, str(r["file_path"]).replace("/", os.sep)))
            self.manifest.append({
                "file_id": str(r["file_id"]).strip(),
                "file_path": fpath,
                "origin": str(r["origin"]).strip(),
                "captured_at": str(r["captured_at"]).strip(),
                "ext": os.path.splitext(fpath)[1].lower()
            })
        self.manifest.sort(key=lambda x: x["captured_at"])
        
        self.all_observations: List[Dict[str, Any]] = []
        self._build_index()

    def _build_index(self):
        for meta in self.manifest:
            fid = meta["file_id"]
            fpath = meta["file_path"]
            ext = meta["ext"]
            if not os.path.exists(fpath):
                continue
                
            try:
                if ext == ".json":
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._parse_json(meta, data)
                elif ext == ".sql":
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        sql_text = f.read()
                    self._parse_sql(meta, sql_text)
                elif ext == ".txt":
                    with open(fpath, "r", encoding="utf-8") as f:
                        txt = f.read()
                    self._parse_txt(meta, txt)
                elif ext == ".log":
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [l.strip() for l in f if l.strip()]
                    self._parse_log(meta, lines)
                elif ext == ".pdf":
                    reader = PdfReader(fpath)
                    text = "\n".join([page.extract_text() or "" for page in reader.pages])
                    self._parse_pdf(meta, text)
            except Exception as e:
                pass

        self._index_system_activity()

    def _parse_json(self, meta: Dict[str, Any], data: Any):
        fid = meta["file_id"]
        cat_time = meta["captured_at"]
        
        # 1. service_resource_export
        if isinstance(data, dict) and "service_exports" in data:
            sexp = data["service_exports"]
            # account_service
            for item in sexp.get("account_service", {}).get("profile_lookups", []):
                res_id = item.get("resource_id")
                sc = item.get("status_code")
                prof = item.get("profile") or {}
                em = prof.get("email")
                uid = prof.get("customer_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "account_service",
                    "resource_id": res_id,
                    "category": "USER_PROFILE",
                    "user_id": uid,
                    "email": em.lower() if em else None,
                    "state": "ABSENT" if sc == 404 else "PRESENT",
                    "pii_exposed": sc == 200,
                    "details": item
                })
            # analytics_platform
            for item in sexp.get("analytics_platform", {}).get("profiles", []):
                res_id = item.get("resource_id")
                em = item.get("email")
                uid = item.get("customer_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "analytics_platform",
                    "resource_id": res_id,
                    "category": "ANALYTICS_PROFILE",
                    "user_id": uid,
                    "email": em.lower() if em else None,
                    "state": "PRESENT" if em else "ANONYMIZED",
                    "pii_exposed": bool(em),
                    "details": item
                })
            # backup_service
            for item in sexp.get("backup_service", {}).get("restore_entries", []):
                res_id = item.get("resource_id")
                rest_allowed = item.get("restore_allowed")
                em = item.get("customer_email")
                uid = item.get("customer_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "backup_service",
                    "resource_id": res_id,
                    "category": "BACKUP_ARCHIVE",
                    "user_id": uid,
                    "email": em.lower() if em else None,
                    "state": "ACTIVE" if rest_allowed else "BLOCKED",
                    "restore_allowed": rest_allowed,
                    "details": item
                })
            # export_service
            for item in sexp.get("export_service", {}).get("exports", []):
                res_id = item.get("resource_id")
                em = item.get("owner_email")
                uid = item.get("customer_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "export_service",
                    "resource_id": res_id,
                    "category": "USER_EXPORT",
                    "user_id": uid,
                    "email": em.lower() if em else None,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "details": item
                })
            # integration_service
            for item in sexp.get("integration_service", {}).get("connectors", []):
                res_id = item.get("resource_id")
                enabled = item.get("enabled")
                em = item.get("customer_email")
                uid = item.get("customer_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "integration_service",
                    "resource_id": res_id,
                    "category": "CUSTOMER_DATA_FLOW",
                    "user_id": uid,
                    "email": em.lower() if em else None,
                    "state": "ACTIVE" if enabled else "DISABLED",
                    "enabled": enabled,
                    "details": item
                })
            # search_service
            for item in sexp.get("search_service", {}).get("index_queries", []):
                res_id = item.get("resource_id")
                hits = item.get("hits", {})
                docs = hits.get("documents", [])
                tot = hits.get("total", 0)
                doc_em = docs[0].get("email") if docs else item.get("query")
                doc_uid = docs[0].get("customer_reference") if docs else None
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "search_service",
                    "resource_id": res_id,
                    "category": "SEARCH_INDEX_ENTRY",
                    "user_id": doc_uid,
                    "email": doc_em.lower() if doc_em else None,
                    "state": "PRESENT" if tot > 0 else "ABSENT",
                    "pii_exposed": tot > 0,
                    "details": item
                })
            # security_service
            for item in sexp.get("security_service", {}).get("audit_records", []):
                res_id = item.get("resource_id")
                uid = item.get("subject_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "security_service",
                    "resource_id": res_id,
                    "category": "SECURITY_AUDIT_LOG",
                    "user_id": uid,
                    "email": None,
                    "state": "PRESENT",
                    "retention_until": item.get("retention_until"),
                    "details": item
                })
            # support_platform
            for item in sexp.get("support_platform", {}).get("tickets", []):
                res_id = item.get("resource_id")
                em = item.get("requester_email")
                uid = item.get("customer_reference")
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "support_platform",
                    "resource_id": res_id,
                    "category": "SUPPORT_MESSAGE",
                    "user_id": uid,
                    "email": em.lower() if em else None,
                    "state": "PRESENT" if em else "REDACTED",
                    "pii_exposed": bool(em),
                    "details": item
                })

        # 2. customer_data_snapshot_bundle
        if isinstance(data, dict) and "snapshots" in data:
            for snap in data["snapshots"]:
                records = snap.get("records", [])
                for rec in records:
                    res_id = rec.get("resource_id", "")
                    uid = rec.get("subject_reference") or rec.get("user_id")
                    em = rec.get("email")
                    if res_id.startswith("tombstone"):
                        pii = any(rec.get(k) is not None for k in ["name", "email", "phone", "email_hash"])
                        self.all_observations.append({
                            "evidence_id": fid,
                            "captured_at": cat_time,
                            "system_id": "identity_service",
                            "resource_id": res_id,
                            "category": "ACCOUNT_TOMBSTONE",
                            "user_id": uid,
                            "email": em.lower() if em else None,
                            "state": "PRESENT" if pii else "REDACTED",
                            "pii_exposed": pii,
                            "details": rec
                        })
                    elif res_id.startswith("audit_record"):
                        self.all_observations.append({
                            "evidence_id": fid,
                            "captured_at": cat_time,
                            "system_id": "security_service",
                            "resource_id": res_id,
                            "category": "SECURITY_AUDIT_LOG",
                            "user_id": uid,
                            "email": None,
                            "state": "PRESENT",
                            "details": rec
                        })

        # 3. records files (e.g. customer_analytics_report, customer_export_jobs)
        if isinstance(data, dict) and "records" in data:
            for rec in data["records"]:
                res_id = rec.get("resource_id", "")
                uid = rec.get("user_id") or rec.get("subject_reference")
                em = rec.get("email") or rec.get("owner_email") or rec.get("subject_reference")
                em_str = em.lower() if (em and "@" in str(em)) else None
                
                if res_id.startswith("analytics_"):
                    pii = any(rec.get(k) is not None for k in ["email", "user_id", "phone", "email_hash"])
                    self.all_observations.append({
                        "evidence_id": fid,
                        "captured_at": cat_time,
                        "system_id": "analytics_platform",
                        "resource_id": res_id,
                        "category": "ANALYTICS_PROFILE",
                        "user_id": uid,
                        "email": em_str,
                        "state": "PRESENT" if pii else "ANONYMIZED",
                        "pii_exposed": pii,
                        "details": rec
                    })
                elif res_id.startswith("export_"):
                    self.all_observations.append({
                        "evidence_id": fid,
                        "captured_at": cat_time,
                        "system_id": "export_service",
                        "resource_id": res_id,
                        "category": "USER_EXPORT",
                        "user_id": uid,
                        "email": em_str,
                        "state": "PRESENT",
                        "pii_exposed": True,
                        "details": rec
                    })
                elif res_id.startswith("account_"):
                    res_val = rec.get("result", "")
                    self.all_observations.append({
                        "evidence_id": fid,
                        "captured_at": cat_time,
                        "system_id": "account_service",
                        "resource_id": res_id,
                        "category": "USER_PROFILE",
                        "user_id": uid if (uid and uid.startswith("user_")) else None,
                        "email": em_str,
                        "state": "ABSENT" if res_val == "NOT_FOUND" else "PRESENT",
                        "pii_exposed": res_val != "NOT_FOUND",
                        "details": rec
                    })

    def _parse_sql(self, meta: Dict[str, Any], text: str):
        fid = meta["file_id"]
        cat_time = meta["captured_at"]
        insert_re = re.compile(r"INSERT INTO\s+[\"']?(\w+)[\"']?\s+VALUES\s*\((.*?)\);", re.IGNORECASE)
        for match in insert_re.finditer(text):
            tbl = match.group(1).lower()
            vals_str = match.group(2)
            vals = []
            for v in re.split(r",\s*(?=(?:[^']*'[^']*')*[^']*$)", vals_str):
                v = v.strip().strip("'\"")
                vals.append(None if v == "NULL" else v)
            if not vals:
                continue

            res_id = vals[0]
            if "customer_profiles" in tbl or "profiles" in tbl or "customer_data" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                # search for email among values
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "account_service",
                    "resource_id": res_id,
                    "category": "USER_PROFILE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "details": {"table": tbl, "values": vals}
                })
            elif "backup_restore_entries" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                rest_allowed = any(v in ["1", 1, "true", True] for v in vals[3:5])
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "backup_service",
                    "resource_id": res_id,
                    "category": "BACKUP_ARCHIVE",
                    "user_id": uid,
                    "email": em,
                    "state": "ACTIVE" if rest_allowed else "BLOCKED",
                    "restore_allowed": rest_allowed,
                    "details": {"table": tbl, "values": vals}
                })
            elif "search_documents" in tbl or "customer_search" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "search_service",
                    "resource_id": res_id,
                    "category": "SEARCH_INDEX_ENTRY",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "details": {"table": tbl, "values": vals}
                })
            elif "analytics_profiles" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "analytics_platform",
                    "resource_id": res_id,
                    "category": "ANALYTICS_PROFILE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT" if em else "ANONYMIZED",
                    "pii_exposed": bool(em),
                    "details": {"table": tbl, "values": vals}
                })
            elif "connector_subscriptions" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                enabled = any(v in ["1", 1, "true", True] for v in vals[3:5])
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "integration_service",
                    "resource_id": res_id,
                    "category": "CUSTOMER_DATA_FLOW",
                    "user_id": uid,
                    "email": em,
                    "state": "ACTIVE" if enabled else "DISABLED",
                    "enabled": enabled,
                    "details": {"table": tbl, "values": vals}
                })
            elif "customer_exports" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "export_service",
                    "resource_id": res_id,
                    "category": "USER_EXPORT",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "details": {"table": tbl, "values": vals}
                })
            elif "security_audit_records" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "security_service",
                    "resource_id": res_id,
                    "category": "SECURITY_AUDIT_LOG",
                    "user_id": uid,
                    "email": None,
                    "state": "PRESENT",
                    "details": {"table": tbl, "values": vals}
                })
            elif "support_records" in tbl:
                uid = vals[1] if len(vals) > 1 and str(vals[1]).startswith("user_") else None
                em = next((v.lower() for v in vals if v and "@" in str(v)), None)
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": "support_platform",
                    "resource_id": res_id,
                    "category": "SUPPORT_MESSAGE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT" if em else "REDACTED",
                    "pii_exposed": bool(em),
                    "details": {"table": tbl, "values": vals}
                })

    def _parse_txt(self, meta: Dict[str, Any], text: str):
        fid = meta["file_id"]
        cat_time = meta["captured_at"]
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("- "):
                continue
            parts = [p.strip() for p in line[2:].split("|")]
            if len(parts) >= 6:
                ts, sys_id, res_id, cat, status, ident = parts[:6]
                uid = ident if ident.startswith("user_") else None
                em = ident.lower() if "@" in ident else None
                pii = (status in ["FOUND", "IDENTIFIABLE", "ACTIVE"])
                state = "PRESENT"
                if status == "NOT_FOUND":
                    state = "ABSENT"
                elif status in ["ANONYMIZED", "REDACTED", "DISABLED", "BLOCKED"]:
                    state = status
                elif status == "ACTIVE":
                    state = "ACTIVE"
                    
                self.all_observations.append({
                    "evidence_id": fid,
                    "captured_at": cat_time,
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "category": cat,
                    "user_id": uid,
                    "email": em,
                    "status_label": status,
                    "state": state,
                    "pii_exposed": pii,
                    "details": line
                })

    def _parse_log(self, meta: Dict[str, Any], lines: List[str]):
        fid = meta["file_id"]
        cat_time = meta["captured_at"]
        for line in lines:
            sys_m = re.search(r"service=([a-zA-Z0-9_]+)", line)
            res_m = re.search(r"resource_id=([a-zA-Z0-9_]+)", line)
            if not res_m:
                # also check for bracketed formats e.g. [support_platform]
                res_m = re.search(r"\b(support_\d+|account_\d+|search_\d+|analytics_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|export_\d+)\b", line)
            if not res_m:
                continue
                
            res_id = res_m.group(1)
            sys_id = sys_m.group(1) if sys_m else None
            if not sys_id:
                if res_id.startswith("support_"): sys_id = "support_platform"
                elif res_id.startswith("account_"): sys_id = "account_service"
                elif res_id.startswith("search_"): sys_id = "search_service"
                elif res_id.startswith("analytics_"): sys_id = "analytics_platform"
                elif res_id.startswith("data_flow_"): sys_id = "integration_service"
                elif res_id.startswith("backup_"): sys_id = "backup_service"
                elif res_id.startswith("audit_record_"): sys_id = "security_service"
                elif res_id.startswith("export_"): sys_id = "export_service"
                else: sys_id = "generic_service"
            
            em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", line)
            em = em_m.group(1).lower() if em_m else None
            
            uid_m = re.search(r"\b(user_\d+)\b", line)
            uid = uid_m.group(1) if uid_m else None
            
            state = "PRESENT"
            pii = False
            cat = "GENERIC"
            if sys_id == "account_service":
                cat = "USER_PROFILE"
                if "http_status=404" in line or "rows=0" in line:
                    state = "ABSENT"
                else:
                    state = "PRESENT"
                    pii = True
            elif sys_id == "search_service":
                cat = "SEARCH_INDEX_ENTRY"
                if "result=hit" in line or "total_hits=1" in line:
                    state = "PRESENT"
                    pii = True
                else:
                    state = "ABSENT"
            elif sys_id == "support_platform":
                cat = "SUPPORT_MESSAGE"
                if "requester_email=null" in line or "requester_email=\"\"" in line or (em is None and uid):
                    state = "REDACTED"
                else:
                    state = "PRESENT"
                    pii = True
            elif sys_id == "analytics_platform":
                cat = "ANALYTICS_PROFILE"
                if "email=null" in line or "email=\"\"" in line or (em is None and uid):
                    state = "ANONYMIZED"
                else:
                    state = "PRESENT"
                    pii = True
            elif sys_id == "integration_service":
                cat = "CUSTOMER_DATA_FLOW"
                if "enabled=true" in line:
                    state = "ACTIVE"
                    pii = True
                else:
                    state = "DISABLED"
            elif sys_id == "backup_service":
                cat = "BACKUP_ARCHIVE"
                if "restore_allowed=true" in line:
                    state = "ACTIVE"
                else:
                    state = "BLOCKED"
            elif sys_id == "security_service":
                cat = "SECURITY_AUDIT_LOG"
                state = "PRESENT"

            self.all_observations.append({
                "evidence_id": fid,
                "captured_at": cat_time,
                "system_id": sys_id,
                "resource_id": res_id,
                "category": cat,
                "user_id": uid,
                "email": em,
                "state": state,
                "pii_exposed": pii,
                "details": line
            })

    def _parse_pdf(self, meta: Dict[str, Any], text: str):
        fid = meta["file_id"]
        cat_time = meta["captured_at"]
        res_m = re.search(r"\b(support_\d+|account_\d+|export_\d+)\b", text)
        uid_m = re.search(r"\b(user_\d+)\b", text)
        em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
        
        if res_m:
            res_id = res_m.group(1)
            sys_id = "support_platform" if "support" in res_id else "account_service"
            cat = "SUPPORT_ATTACHMENT" if "support" in res_id else "USER_PROFILE"
            self.all_observations.append({
                "evidence_id": fid,
                "captured_at": cat_time,
                "system_id": sys_id,
                "resource_id": res_id,
                "category": cat,
                "user_id": uid_m.group(1) if uid_m else None,
                "email": em_m.group(1).lower() if em_m else None,
                "state": "PRESENT",
                "pii_exposed": True,
                "details": text[:200]
            })

    def _index_system_activity(self):
        for idx, r in self.df_activity.iterrows():
            aid = str(r["activity_id"]).strip()
            etime = str(r["event_time"]).strip()
            etype = str(r["event_type"]).strip()
            src = str(r["source_system"]).strip()
            tgt = str(r["target_system"]).strip()
            res_id = str(r["resource_id"]).strip()
            res_val = str(r["reported_result"]).strip()
            details = str(r["details"]).strip() if pd.notna(r["details"]) else ""
            
            em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", details)
            em = em_m.group(1).lower() if em_m else None
            
            uid_m = re.search(r"\b(user_\d+)\b", details)
            uid = uid_m.group(1) if uid_m else None
            
            self.all_observations.append({
                "evidence_id": aid,
                "captured_at": etime,
                "system_id": tgt,
                "resource_id": res_id,
                "category": "SYSTEM_ACTIVITY",
                "user_id": uid,
                "email": em,
                "state": res_val,
                "event_type": etype,
                "details": details
            })

    def get_observations_for_subject(
        self,
        user_id: str,
        emails: Set[str],
        audit_at: str
    ) -> List[Dict[str, Any]]:
        results = []
        emails_lower = {e.lower() for e in emails if e}
        
        for ob in self.all_observations:
            if ob["captured_at"] > audit_at:
                continue
                
            matched = False
            if ob["user_id"] and ob["user_id"] == user_id:
                matched = True
            elif ob["email"] and ob["email"].lower() in emails_lower:
                matched = True
                
            if matched:
                results.append(ob)
                
        return results
