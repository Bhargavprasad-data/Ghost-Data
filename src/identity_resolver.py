"""
Identity Resolver Module
Reconstructs subject identity graph from current user identities and historical audit logs.
Resolves case-insensitive emails, previous emails, user_id, phone, and email hashes.
"""

import os
import pandas as pd
from typing import Dict, Set, Optional, List, Any

class IdentityResolver:
    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.users_path = os.path.join(dataset_dir, "user_identities.csv")
        self.audit_path = os.path.join(dataset_dir, "user_audit_log.csv")
        
        self.df_users = pd.read_csv(self.users_path)
        self.df_audit = pd.read_csv(self.audit_path)
        
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.email_to_user: Dict[str, str] = {}
        self.phone_to_user: Dict[str, str] = {}
        self.hash_to_user: Dict[str, str] = {}
        
        self._build_identity_graph()

    def _build_identity_graph(self):
        # 1. Base identities from user_identities.csv
        for idx, r in self.df_users.iterrows():
            uid = str(r["user_id"]).strip()
            name = str(r["name"]).strip() if pd.notna(r["name"]) else None
            email = str(r["email"]).strip() if pd.notna(r["email"]) else None
            phone = str(r["phone"]).strip() if pd.notna(r["phone"]) else None
            em_hash = str(r["email_hash"]).strip() if pd.notna(r["email_hash"]) else None
            updated_at = str(r["updated_at"]).strip() if pd.notna(r["updated_at"]) else None
            
            profile = {
                "user_id": uid,
                "name": name,
                "current_email": email,
                "current_phone": phone,
                "current_email_hash": em_hash,
                "all_emails": set([email.lower()]) if email else set(),
                "all_phones": set([phone]) if phone else set(),
                "all_hashes": set([em_hash.lower()]) if em_hash else set(),
                "history": [],
                "updated_at": updated_at
            }
            self.user_profiles[uid] = profile
            
            if email:
                self.email_to_user[email.lower()] = uid
            if phone:
                self.phone_to_user[phone] = uid
            if em_hash:
                self.hash_to_user[em_hash.lower()] = uid

        # 2. Historical audit log enrichment from user_audit_log.csv
        for idx, r in self.df_audit.iterrows():
            uid = str(r["user_id"]).strip()
            field = str(r["field_name"]).strip()
            old_val = str(r["old_value"]).strip() if pd.notna(r["old_value"]) else None
            new_val = str(r["new_value"]).strip() if pd.notna(r["new_value"]) else None
            etime = str(r["event_time"]).strip() if pd.notna(r["event_time"]) else None
            aid = str(r["audit_id"]).strip()
            
            if uid in self.user_profiles:
                prof = self.user_profiles[uid]
                prof["history"].append({
                    "audit_id": aid,
                    "event_time": etime,
                    "field_name": field,
                    "old_value": old_val,
                    "new_value": new_val
                })
                
                if field == "email":
                    if old_val:
                        prof["all_emails"].add(old_val.lower())
                        self.email_to_user[old_val.lower()] = uid
                    if new_val:
                        prof["all_emails"].add(new_val.lower())
                        self.email_to_user[new_val.lower()] = uid
                elif field == "phone":
                    if old_val:
                        prof["all_phones"].add(old_val)
                        self.phone_to_user[old_val] = uid
                    if new_val:
                        prof["all_phones"].add(new_val)
                        self.phone_to_user[new_val] = uid
                elif field == "email_hash":
                    if old_val:
                        prof["all_hashes"].add(old_val.lower())
                        self.hash_to_user[old_val.lower()] = uid
                    if new_val:
                        prof["all_hashes"].add(new_val.lower())
                        self.hash_to_user[new_val.lower()] = uid

    def resolve(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Resolves an email, phone, user_id, or email_hash to the full Subject Identity Profile.
        Matching is case-insensitive for emails and hashes.
        """
        if not identifier:
            return None
        
        ident = identifier.strip()
        ident_lower = ident.lower()
        
        uid = None
        if ident in self.user_profiles:
            uid = ident
        elif ident_lower in self.email_to_user:
            uid = self.email_to_user[ident_lower]
        elif ident in self.phone_to_user:
            uid = self.phone_to_user[ident]
        elif ident_lower in self.hash_to_user:
            uid = self.hash_to_user[ident_lower]
            
        if not uid or uid not in self.user_profiles:
            return None
            
        p = self.user_profiles[uid]
        return {
            "user_id": p["user_id"],
            "name": p["name"],
            "current_email": p["current_email"],
            "current_phone": p["current_phone"],
            "current_email_hash": p["current_email_hash"],
            "all_emails": sorted(list(p["all_emails"])),
            "all_phones": sorted(list(p["all_phones"])),
            "all_hashes": sorted(list(p["all_hashes"])),
            "history": p["history"],
            "updated_at": p["updated_at"]
        }
