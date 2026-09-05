import hashlib
import json
import time
import re
from typing import Dict, Any, List, Optional

def mask_pii_string(text: str) -> str:
    """Mask email addresses and phone numbers in strings."""
    if not text:
        return text
    # Mask emails
    email_pattern = r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    def mask_email(match):
        name, domain = match.group(1), match.group(2)
        masked_name = name[0] + "***" if len(name) > 1 else "*"
        return f"{masked_name}@{domain}"
    
    text = re.sub(email_pattern, mask_email, text)
    
    # Mask 10-digit Indian phone numbers
    phone_pattern = r'(\+91[\s\-]?)?(\d{2})\d{6}(\d{2})'
    text = re.sub(phone_pattern, r'\1\2******\3', text)
    return text

def mask_pii(data: Any) -> Any:
    """Recursively mask PII fields in dictionaries or lists."""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if k in ['email', 'customer_email', 'user_email']:
                if isinstance(v, str) and '@' in v:
                    parts = v.split('@')
                    masked[k] = parts[0][0] + "***@" + parts[1] if len(parts[0]) > 1 else "*@" + parts[1]
                else:
                    masked[k] = "***"
            elif k in ['phone', 'contact', 'customer_phone']:
                masked[k] = str(v)[:4] + "******" + str(v)[-2:] if len(str(v)) >= 10 else "******"
            elif k in ['card_number', 'account_number']:
                masked[k] = "****-****-****-" + str(v)[-4:] if len(str(v)) >= 4 else "****"
            else:
                masked[k] = mask_pii(v)
        return masked
    elif isinstance(data, list):
        return [mask_pii(item) for item in data]
    elif isinstance(data, str):
        return mask_pii_string(data)
    return data


class AuditLedger:
    def __init__(self, ledger_file: Optional[str] = None):
        self.ledger_file = ledger_file
        self.chain: List[Dict[str, Any]] = []
        self._initialize_genesis_block()

    def _initialize_genesis_block(self):
        genesis_data = {
            "index": 0,
            "timestamp": time.time(),
            "event": "GENESIS",
            "details": "PayRecover AI Genesis Audit Block",
            "previous_hash": "0" * 64
        }
        genesis_data["hash"] = self._calculate_hash(genesis_data)
        self.chain.append(genesis_data)

    def _calculate_hash(self, block: Dict[str, Any]) -> str:
        block_copy = {k: v for k, v in block.items() if k != "hash"}
        encoded = json.dumps(block_copy, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    def append_event(self, event_type: str, transaction_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Add an event to the ledger with SHA-256 hash chaining and PII masking."""
        prev_block = self.chain[-1]
        masked_details = mask_pii(details)
        
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "event": event_type,
            "transaction_id": transaction_id,
            "details": masked_details,
            "previous_hash": prev_block["hash"]
        }
        block["hash"] = self._calculate_hash(block)
        self.chain.append(block)
        
        if self.ledger_file:
            try:
                with open(self.ledger_file, 'w') as f:
                    json.dump(self.chain, f, indent=2)
            except Exception:
                pass
                
        return block

    def verify_integrity(self) -> bool:
        """Verify SHA-256 hash chain integrity of all audit records."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            if current["previous_hash"] != previous["hash"]:
                return False
            if current["hash"] != self._calculate_hash(current):
                return False
        return True

    def get_transaction_history(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Retrieve audit history for a specific transaction."""
        return [block for block in self.chain if block.get("transaction_id") == transaction_id]

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent ledger events."""
        return self.chain[-limit:][::-1]


# Global audit ledger instance
ledger_instance = AuditLedger()
