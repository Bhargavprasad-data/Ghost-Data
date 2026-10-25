import os
import glob
import json
import re
import csv
import pandas as pd
from pypdf import PdfReader

class EvidenceIndex:
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = dataset_dir
        self.df_manifest = pd.read_csv(os.path.join(dataset_dir, "evidence_files.csv"))
        self.manifest = []
        for idx, r in self.df_manifest.iterrows():
            fpath = os.path.normpath(os.path.join(dataset_dir, r["file_path"].replace("/", os.sep)))
            self.manifest.append({
                "file_id": r["file_id"],
                "file_path": fpath,
                "origin": r["origin"],
                "captured_at": r["captured_at"],
                "ext": os.path.splitext(fpath)[1].lower()
            })
        # Sort by captured_at
        self.manifest.sort(key=lambda x: x["captured_at"])
        
        # Cache of parsed files: file_id -> parsed_data
        self.parsed_cache = {}
        self._parse_all_files()

    def _parse_all_files(self):
        print("Parsing evidence files into structured index...")
        for item in self.manifest:
            fid = item["file_id"]
            fpath = item["file_path"]
            ext = item["ext"]
            if not os.path.exists(fpath):
                continue
            
            try:
                if ext == ".json":
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.parsed_cache[fid] = self._parse_json(fid, item, data)
                elif ext == ".sql":
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        sql_text = f.read()
                    self.parsed_cache[fid] = self._parse_sql(fid, item, sql_text)
                elif ext == ".txt":
                    with open(fpath, "r", encoding="utf-8") as f:
                        txt = f.read()
                    self.parsed_cache[fid] = self._parse_txt(fid, item, txt)
                elif ext == ".log":
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [l.strip() for l in f if l.strip()]
                    self.parsed_cache[fid] = self._parse_log(fid, item, lines)
                elif ext == ".pdf":
                    reader = PdfReader(fpath)
                    text = "\n".join([page.extract_text() or "" for page in reader.pages])
                    self.parsed_cache[fid] = self._parse_pdf(fid, item, text)
            except Exception as e:
                print(f"Error parsing {fid} ({fpath}): {e}")
        print(f"Parsed {len(self.parsed_cache)} files.")

    def _parse_json(self, fid, meta, data):
        observations = [] # list of dicts: {system_id, resource_id, category, user_id, email, state, pii_exposed, details}
        # 1. service_resource_export
        if "service_exports" in data:
            sexp = data["service_exports"]
            # account_service
            for item in sexp.get("account_service", {}).get("profile_lookups", []):
                res_id = item.get("resource_id")
                sc = item.get("status_code")
                prof = item.get("profile") or {}
                em = prof.get("email")
                uid = prof.get("customer_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "account_service",
                    "resource_id": res_id,
                    "category": "USER_PROFILE",
                    "user_id": uid,
                    "email": em,
                    "state": "ABSENT" if sc == 404 else "PRESENT",
                    "pii_exposed": sc == 200,
                    "raw": item
                })
            # analytics_platform
            for item in sexp.get("analytics_platform", {}).get("profiles", []):
                res_id = item.get("resource_id")
                em = item.get("email")
                uid = item.get("customer_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "analytics_platform",
                    "resource_id": res_id,
                    "category": "ANALYTICS_PROFILE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT" if em else "ANONYMIZED",
                    "pii_exposed": bool(em),
                    "raw": item
                })
            # backup_service
            for item in sexp.get("backup_service", {}).get("restore_entries", []):
                res_id = item.get("resource_id")
                rest_allowed = item.get("restore_allowed")
                em = item.get("customer_email")
                uid = item.get("customer_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "backup_service",
                    "resource_id": res_id,
                    "category": "BACKUP_ARCHIVE",
                    "user_id": uid,
                    "email": em,
                    "state": "ACTIVE" if rest_allowed else "BLOCKED",
                    "restore_allowed": rest_allowed,
                    "raw": item
                })
            # export_service
            for item in sexp.get("export_service", {}).get("exports", []):
                res_id = item.get("resource_id")
                em = item.get("owner_email")
                uid = item.get("customer_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "export_service",
                    "resource_id": res_id,
                    "category": "USER_EXPORT",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "raw": item
                })
            # integration_service
            for item in sexp.get("integration_service", {}).get("connectors", []):
                res_id = item.get("resource_id")
                enabled = item.get("enabled")
                em = item.get("customer_email")
                uid = item.get("customer_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "integration_service",
                    "resource_id": res_id,
                    "category": "CUSTOMER_DATA_FLOW",
                    "user_id": uid,
                    "email": em,
                    "state": "ACTIVE" if enabled else "DISABLED",
                    "enabled": enabled,
                    "raw": item
                })
            # search_service
            for item in sexp.get("search_service", {}).get("index_queries", []):
                res_id = item.get("resource_id")
                hits = item.get("hits", {})
                docs = hits.get("documents", [])
                tot = hits.get("total", 0)
                doc_em = docs[0].get("email") if docs else item.get("query")
                doc_uid = docs[0].get("customer_reference") if docs else None
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "search_service",
                    "resource_id": res_id,
                    "category": "SEARCH_INDEX_ENTRY",
                    "user_id": doc_uid,
                    "email": doc_em,
                    "state": "PRESENT" if tot > 0 else "ABSENT",
                    "pii_exposed": tot > 0,
                    "raw": item
                })
            # security_service
            for item in sexp.get("security_service", {}).get("audit_records", []):
                res_id = item.get("resource_id")
                uid = item.get("subject_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "security_service",
                    "resource_id": res_id,
                    "category": "SECURITY_AUDIT_LOG",
                    "user_id": uid,
                    "email": None,
                    "state": "PRESENT",
                    "retention_until": item.get("retention_until"),
                    "raw": item
                })
            # support_platform
            for item in sexp.get("support_platform", {}).get("tickets", []):
                res_id = item.get("resource_id")
                em = item.get("requester_email")
                uid = item.get("customer_reference")
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "support_platform",
                    "resource_id": res_id,
                    "category": "SUPPORT_MESSAGE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT" if em else "REDACTED",
                    "pii_exposed": bool(em),
                    "raw": item
                })

        # 2. customer_data_snapshot_bundle
        if "snapshots" in data:
            for snap in data["snapshots"]:
                records = snap.get("records", [])
                for rec in records:
                    res_id = rec.get("resource_id", "")
                    uid = rec.get("subject_reference") or rec.get("user_id")
                    em = rec.get("email")
                    if res_id.startswith("tombstone"):
                        pii = any(rec.get(k) is not None for k in ["name", "email", "phone", "email_hash"])
                        observations.append({
                            "evidence_id": fid,
                            "captured_at": meta["captured_at"],
                            "system_id": "identity_service",
                            "resource_id": res_id,
                            "category": "ACCOUNT_TOMBSTONE",
                            "user_id": uid,
                            "email": em,
                            "state": "PRESENT" if pii else "REDACTED",
                            "pii_exposed": pii,
                            "raw": rec
                        })
                    elif res_id.startswith("audit_record"):
                        observations.append({
                            "evidence_id": fid,
                            "captured_at": meta["captured_at"],
                            "system_id": "security_service",
                            "resource_id": res_id,
                            "category": "SECURITY_AUDIT_LOG",
                            "user_id": uid,
                            "email": None,
                            "state": "PRESENT",
                            "raw": rec
                        })

        return observations

    def _parse_sql(self, fid, meta, text):
        observations = []
        # Parse INSERT INTO statements using regex
        insert_re = re.compile(r"INSERT INTO\s+[\"']?(\w+)[\"']?\s+VALUES\s*\((.*?)\);", re.IGNORECASE)
        for match in insert_re.finditer(text):
            tbl = match.group(1).lower()
            vals_str = match.group(2)
            # split by comma handling quotes
            vals = []
            for v in re.split(r",\s*(?=(?:[^']*'[^']*')*[^']*$)", vals_str):
                v = v.strip().strip("'\"")
                vals.append(None if v == "NULL" else v)
            
            if "customer_profiles" in tbl or "profiles" in tbl:
                # ('account_005', 'user_05', 'Leila Haddad', 'leila.haddad@yahoo.com', ...)
                res_id = vals[0]
                uid = vals[1] if len(vals) > 1 else None
                em = vals[3] if len(vals) > 3 else (vals[2] if len(vals) > 2 else None)
                # check if failover_replica or primary
                status = vals[5] if len(vals) > 5 else "ACTIVE"
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "account_service",
                    "resource_id": res_id,
                    "category": "USER_PROFILE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "table": tbl,
                    "raw": vals
                })
            elif "backup_restore_entries" in tbl:
                res_id = vals[0]
                uid = vals[1]
                em = vals[2]
                rest_allowed = vals[4] in ["1", 1, "true", True]
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "backup_service",
                    "resource_id": res_id,
                    "category": "BACKUP_ARCHIVE",
                    "user_id": uid,
                    "email": em,
                    "state": "ACTIVE" if rest_allowed else "BLOCKED",
                    "restore_allowed": rest_allowed,
                    "raw": vals
                })
            elif "customer_search_documents" in tbl:
                res_id = vals[0]
                uid = vals[1]
                em = vals[3] if len(vals) > 3 else None
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "search_service",
                    "resource_id": res_id,
                    "category": "SEARCH_INDEX_ENTRY",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "raw": vals
                })
            elif "customer_analytics_profiles" in tbl:
                res_id = vals[0]
                uid = vals[1]
                em = vals[2]
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "analytics_platform",
                    "resource_id": res_id,
                    "category": "ANALYTICS_PROFILE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT" if em else "ANONYMIZED",
                    "pii_exposed": bool(em),
                    "raw": vals
                })
            elif "connector_subscriptions" in tbl:
                res_id = vals[0]
                uid = vals[1]
                em = vals[2]
                enabled = vals[4] in ["1", 1, "true", True]
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "integration_service",
                    "resource_id": res_id,
                    "category": "CUSTOMER_DATA_FLOW",
                    "user_id": uid,
                    "email": em,
                    "state": "ACTIVE" if enabled else "DISABLED",
                    "enabled": enabled,
                    "raw": vals
                })
            elif "customer_exports" in tbl:
                res_id = vals[0]
                uid = vals[1]
                em = vals[2]
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "export_service",
                    "resource_id": res_id,
                    "category": "USER_EXPORT",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT",
                    "pii_exposed": True,
                    "raw": vals
                })
            elif "security_audit_records" in tbl:
                res_id = vals[0]
                uid = vals[1]
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "security_service",
                    "resource_id": res_id,
                    "category": "SECURITY_AUDIT_LOG",
                    "user_id": uid,
                    "email": None,
                    "state": "PRESENT",
                    "retention_until": vals[3] if len(vals) > 3 else None,
                    "raw": vals
                })
            elif "support_records" in tbl:
                res_id = vals[0]
                uid = vals[1]
                em = vals[3] if len(vals) > 3 else None
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": "support_platform",
                    "resource_id": res_id,
                    "category": "SUPPORT_MESSAGE",
                    "user_id": uid,
                    "email": em,
                    "state": "PRESENT" if em else "REDACTED",
                    "pii_exposed": bool(em),
                    "raw": vals
                })
        return observations

    def _parse_txt(self, fid, meta, text):
        observations = []
        # format: - 2026-10-01T12:00:00Z | system_id | resource_id | category | status | identifier
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("- "):
                continue
            parts = [p.strip() for p in line[2:].split("|")]
            if len(parts) >= 6:
                ts, sys_id, res_id, cat, status, ident = parts[:6]
                uid = ident if ident.startswith("user_") else None
                em = ident if "@" in ident else None
                pii = (status in ["FOUND", "IDENTIFIABLE", "ACTIVE"])
                state = "PRESENT"
                if status == "NOT_FOUND":
                    state = "ABSENT"
                elif status in ["ANONYMIZED", "REDACTED", "DISABLED", "BLOCKED"]:
                    state = status
                elif status == "ACTIVE":
                    state = "ACTIVE"
                elif status in ["FOUND", "IDENTIFIABLE"]:
                    state = "PRESENT"
                    
                observations.append({
                    "evidence_id": fid,
                    "captured_at": meta["captured_at"],
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "category": cat,
                    "user_id": uid,
                    "email": em,
                    "status_label": status,
                    "state": state,
                    "pii_exposed": pii,
                    "raw": line
                })
        return observations

    def _parse_log(self, fid, meta, lines):
        observations = []
        for line in lines:
            # key-value pair log line parser
            # e.g.: service=account_service event=profile_lookup_completed resource_id=account_7566 rows=0 http_status=404
            sys_m = re.search(r"service=([a-zA-Z0-9_]+)", line)
            res_m = re.search(r"resource_id=([a-zA-Z0-9_]+)", line)
            if not sys_m or not res_m:
                continue
            sys_id = sys_m.group(1)
            res_id = res_m.group(1)
            
            em_m = re.search(r"(?:email|lookup_key|subject_key|requester_email|customer_email)=([^\s\"]+)", line)
            em = em_m.group(1) if em_m and "@" in em_m.group(1) else None
            
            uid_m = re.search(r"(?:customer_reference|subject_reference|lookup_key)=(user_\d+)", line)
            uid = uid_m.group(1) if uid_m else None
            
            # Check state
            state = "PRESENT"
            pii = False
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
            else:
                cat = "GENERIC"

            observations.append({
                "evidence_id": fid,
                "captured_at": meta["captured_at"],
                "system_id": sys_id,
                "resource_id": res_id,
                "category": cat,
                "user_id": uid,
                "email": em,
                "state": state,
                "pii_exposed": pii,
                "raw": line
            })
        return observations

    def _parse_pdf(self, fid, meta, text):
        observations = []
        # Look for references like support_001, user_18, statement NST-..., CS-4827
        res_m = re.search(r"\b(support_\d+|account_\d+|export_\d+)\b", text)
        uid_m = re.search(r"\b(user_\d+)\b", text)
        em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
        
        if res_m:
            res_id = res_m.group(1)
            sys_id = "support_platform" if "support" in res_id else "account_service"
            cat = "SUPPORT_ATTACHMENT" if "support" in res_id else "USER_PROFILE"
            observations.append({
                "evidence_id": fid,
                "captured_at": meta["captured_at"],
                "system_id": sys_id,
                "resource_id": res_id,
                "category": cat,
                "user_id": uid_m.group(1) if uid_m else None,
                "email": em_m.group(1) if em_m else None,
                "state": "PRESENT",
                "pii_exposed": True,
                "raw": text[:200]
            })
        return observations

if __name__ == "__main__":
    idx = EvidenceIndex()
