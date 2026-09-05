import pytest
from app.audit.ledger import AuditLedger, mask_pii

def test_ledger_hash_chain_integrity():
    ledger = AuditLedger()
    ledger.append_event("TEST_EVENT_1", "tx_101", {"amount": 500, "email": "test@example.com"})
    ledger.append_event("TEST_EVENT_2", "tx_102", {"amount": 1500, "status": "RECOVERED"})
    
    assert len(ledger.chain) == 3  # Genesis + 2 events
    assert ledger.verify_integrity() is True

def test_ledger_tamper_detection():
    ledger = AuditLedger()
    ledger.append_event("TEST_EVENT_1", "tx_101", {"amount": 500})
    ledger.append_event("TEST_EVENT_2", "tx_102", {"amount": 1500})
    
    # Tamper with block 1 payload
    ledger.chain[1]["details"]["amount"] = 99999
    
    # Verification should now fail
    assert ledger.verify_integrity() is False

def test_pii_masking_utility():
    data = {
        "customer_email": "john.doe@company.com",
        "customer_phone": "+919876543210",
        "nested": {
            "email": "jane@domain.in"
        }
    }
    masked = mask_pii(data)
    assert masked["customer_email"] == "j***@company.com"
    assert "9876543210" not in masked["customer_phone"]
    assert masked["nested"]["email"] == "j***@domain.in"
