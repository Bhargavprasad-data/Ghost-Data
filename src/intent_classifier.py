"""
Intent Classifier Module
Determines if request_text authorizes deletion or represents a non-deletion request
(e.g., phone update, data export, invoice copy, email change, marketing opt-out, access request).
Multilingual support for English, Spanish, French, Portuguese, Korean, and Japanese.
"""

import re
from typing import Dict, Any, Tuple

class IntentClassifier:
    def __init__(self):
        # Explicit non-deletion patterns across supported languages
        self.non_deletion_markers = [
            # English
            r"leave\s+the\s+account\s+active",
            r"keep\s+the\s+account\s+as\s+it\s+is",
            r"leave\s+my\s+profile.*?in\s+place",
            r"do\s+not\s+close\s+the\s+account",
            r"without\s+removing\s+the\s+account",
            r"want\s+to\s+continue\s+using\s+the\s+service",
            r"still\s+use\s+this\s+profile",
            r"send\s+me\s+a\s+copy\s+of\s+the\s+information",
            r"still\s+want\s+receipts",
            r"still\s+need\s+the\s+account",
            r"access\s+request,\s+not\s+a\s+deletion",
            r"what\s+personal\s+information\s+you\s+hold",
            r"remove\s+me\s+from\s+marketing\s+lists\s+only",
            r"stop\s+the\s+promotional\s+emails",
            r"mobile\s+number.*?replace\s+it\s+with\s+the\s+new\s+one",
            r"download\s+my\s+account\s+information\s+in\s+a\s+portable\s+format",
            r"copy\s+of\s+last\s+year'?s\s+invoices",
            r"surname\s+is\s+misspelled.*?correct\s+it\s+without",
            r"need\s+help\s+resetting\s+the\s+login",
            
            # Spanish
            r"mantener\s+la\s+cuenta\s+activa",
            r"no\s+cierre[n]?\s+la\s+cuenta",
            r"sin\s+eliminar\s+la\s+cuenta",
            r"solo\s+solicito\s+acceso",
            r"solo\s+quiero\s+darme\s+de\s+baja\s+de\s+publicidad",
            r"actualizar\s+mi\s+tel[eé]fono.*?dejar\s+la\s+cuenta",
            r"copia\s+de\s+mis\s+facturas.*?dejar\s+mi\s+perfil",
            
            # French
            r"laisser\s+le\s+compte\s+actif",
            r"ne\s+fermez\s+pas\s+le\s+compte",
            r"garder\s+le\s+compte\s+tel\s+quel",
            r"sans\s+supprimer\s+le\s+compte",
            r"demande\s+d['’]acc[eè]s.*?non\s+une\s+suppression",
            r"uniquement\s+les\s+emails\s+promotionnels",
            
            # Portuguese
            r"manter\s+a\s+conta\s+ativa",
            r"n[aã]o\s+encerre[m]?\s+a\s+conta",
            r"sem\s+excluir\s+a\s+conta",
            r"apenas\s+acesso.*?n[aã]o\s+exclus[aã]o",
            r"continuar\s+usando\s+o\s+servi[cç]o",
            
            # Korean
            r"계정을\s*유지",
            r"계정을\s*닫지\s*마",
            r"탈퇴가\s*아닌",
            r"조회\s*요청",
            r"수정만",
            
            # Japanese
            r"アカウントを?維持",
            r"アカウントを?削除しないで",
            r"削除ではなく",
            r"アクセス請求",
            r"変更のみ"
        ]
        
        self.compiled_markers = [re.compile(p, re.IGNORECASE) for p in self.non_deletion_markers]

    def is_deletion_authorized(self, request_text: str) -> Tuple[bool, str]:
        """
        Returns (is_authorized, reason)
        If False -> NOT_APPLICABLE
        """
        if not request_text:
            return False, "EMPTY_REQUEST"
            
        cleaned = request_text.strip()
        
        for marker in self.compiled_markers:
            if marker.search(cleaned):
                return False, f"NON_DELETION_INTENT: {marker.pattern}"
                
        # Must authorize deletion/erasure/close/suppression/exclusión/supprimer/삭제/削除
        deletion_keywords = [
            "delet", "eras", "remov", "close my account", "purge", "wipe", "forget",
            "elimina", "borra", "cerrar mi cuenta",
            "supprim", "suppress", "fermer mon compte", "effac",
            "exclui", "exclus", "apaga", "encerrar minha conta",
            "삭제", "탈퇴", "지워",
            "削除", "消去", "解約"
        ]
        
        text_lower = cleaned.lower()
        has_deletion_intent = any(kw in text_lower for kw in deletion_keywords)
        
        if not has_deletion_intent:
            return False, "NO_DELETION_KEYWORD_DETECTED"
            
        return True, "AUTHORIZED_DELETION"
