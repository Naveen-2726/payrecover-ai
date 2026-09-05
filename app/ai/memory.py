import hashlib
from typing import Any, Dict


class BoundedAgentMemory:
    """Privacy-safe in-memory customer recovery preferences and outcomes."""

    def __init__(self):
        self.records: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def key(customer_key: str) -> str:
        return hashlib.sha256(str(customer_key).encode("utf-8")).hexdigest()[:16]

    def remember(self, customer_key: str, preferred_method: str, successful_action: str, contact_count: int = 0) -> Dict[str, Any]:
        memory_key = self.key(customer_key)
        self.records[memory_key] = {
            "memory_key": memory_key,
            "preferred_method": preferred_method,
            "last_successful_action": successful_action,
            "contact_count": max(0, int(contact_count)),
            "synthetic_demo_data": True,
        }
        return self.records[memory_key]

    def recall(self, customer_key: str) -> Dict[str, Any]:
        memory_key = self.key(customer_key)
        return self.records.get(memory_key, {"memory_key": memory_key, "found": False, "synthetic_demo_data": True})


agent_memory = BoundedAgentMemory()
