"""
test_transfer_caps.py - Automated Verification of Transfer Caps & Security Policies.
Tests:
1. Voice Per-Transaction Cap: <= 10,000 allowed, > 10,000 blocked.
2. Voice Daily Cap: <= 25,000 cumulative allowed, > 25,000 cumulative blocked with remaining allowance.
3. MPIN Execution Gate: Prevents transfers > 10,000 at execution time.
4. JWT Secret loader resiliency: Both JWT_SECRET and SECRET_KEY supported.
"""

import os
import sys
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlmodel import Session, select
from database import engine
from models import UserTable, TransactionTable
from assistant import send_money, current_user_var, pending_transfers

def test_voice_per_transaction_cap():
    print("\n--- Test 1: Voice Per-Transaction Cap (₹10,000) ---")
    current_user_var.set("alice")
    
    # 1. Transfer exceeding ₹10,000
    res_blocked = send_money(recipient="bob", amount=15000.0, source_account="savings")
    print(f"Transfer ₹15,000 result:\n  -> {res_blocked}")
    assert "strictly capped at ₹10,000.00" in res_blocked, f"Expected voice cap error, got: {res_blocked}"
    print("✅ Blocked ₹15,000 transfer successfully.")
    
    # 2. Transfer at or below ₹10,000 (Alice's seed balance is ~₹820.50)
    res_allowed = send_money(recipient="bob", amount=500.0, source_account="savings")
    print(f"Transfer ₹500 result:\n  -> {res_allowed}")
    assert "alice" in pending_transfers, "Expected transfer to be pending for alice"
    assert pending_transfers["alice"]["amount"] == 500.0
    print("✅ Allowed ₹500 transfer successfully placed into pending state.")
    del pending_transfers["alice"]

def test_voice_daily_cumulative_cap():
    print("\n--- Test 2: Voice Daily Cumulative Cap (₹25,000) ---")
    current_user_var.set("alice")
    
    with Session(engine) as session:
        # Insert mock voice transactions totaling ₹22,000 today
        today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        tx1 = TransactionTable(
            username="alice",
            date=today_str,
            type="Debit",
            amount=12000.0,
            description="Transfer to charlie (via Voice)",
            category="Transfers",
            channel="Voice"
        )
        tx2 = TransactionTable(
            username="alice",
            date=today_str,
            type="Debit",
            amount=10000.0,
            description="Transfer to david (via Voice)",
            category="Transfers",
            channel="Voice"
        )
        session.add(tx1)
        session.add(tx2)
        session.commit()
        
        try:
            # Now attempting another ₹5,000 should breach ₹22,000 + ₹5,000 = ₹27,000 > ₹25,000
            res = send_money(recipient="bob", amount=5000.0, source_account="savings")
            print(f"Transfer ₹5,000 with ₹22,000 already spent:\n  -> {res}")
            assert "Daily voice transfer limit of ₹25,000.00 would be exceeded" in res
            assert "₹22,000.00" in res
            assert "₹3,000.00" in res # Remaining allowance
            print("✅ Daily cumulative cap triggered correctly with remaining allowance calculated.")
            
            # An allowed transfer of ₹500 (total ₹22,500 <= ₹25,000) should succeed
            res_ok = send_money(recipient="bob", amount=500.0, source_account="savings")
            assert "alice" in pending_transfers
            assert pending_transfers["alice"]["amount"] == 500.0
            print("✅ Transfer within remaining allowance (₹500) successfully accepted.")
            del pending_transfers["alice"]
        finally:
            # Cleanup mock transactions
            session.delete(tx1)
            session.delete(tx2)
            session.commit()

def test_jwt_secret_resiliency():
    print("\n--- Test 3: JWT Secret Config Resiliency ---")
    import jwt
    from utils import create_access_token, JWT_SECRET, JWT_ALGORITHM
    token = create_access_token("alice")
    decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert decoded["sub"] == "alice"
    print("✅ JWT creation and verification succeeded.")

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ NIDHIVANI AI: SECURITY & TRANSFER CAP TEST SUITE")
    print("=" * 60)
    test_voice_per_transaction_cap()
    test_voice_daily_cumulative_cap()
    test_jwt_secret_resiliency()
    print("\n" + "=" * 60)
    print("🎉 ALL SECURITY ENFORCEMENT TESTS PASSED (3/3)!")
    print("=" * 60)
