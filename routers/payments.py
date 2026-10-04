import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from database import get_db_session
from models import UserTable, TransactionTable
from schemas import DirectPaymentRequest

router = APIRouter()

from utils import get_current_user

MAX_IMPS_PER_TX = 200000.0
MAX_IMPS_DAILY_LIMIT = 500000.0

@router.post("/api/payments/transfer")
async def direct_transfer_endpoint(
    request: DirectPaymentRequest, 
    session: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    sender_username = request.username.lower().strip()
    if sender_username != current_user:
        raise HTTPException(status_code=403, detail="Forbidden: You can only transfer money from your own authenticated account.")
    recipient_username = request.recipient_username.lower().strip()
    
    if sender_username == recipient_username:
        raise HTTPException(status_code=400, detail="Cannot transfer money to yourself.")
        
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive.")

    # Enforce IMPS limits from banking operations policy
    if request.amount > MAX_IMPS_PER_TX:
        raise HTTPException(
            status_code=400, 
            detail=f"Transfer amount exceeds maximum per-transaction limit of ₹{MAX_IMPS_PER_TX:,.2f}."
        )

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    recent_txs = session.exec(
        select(TransactionTable).where(
            TransactionTable.username == sender_username,
            TransactionTable.type.ilike("debit"),
            TransactionTable.date.like(f"{today_str}%")
        )
    ).all()
    daily_spent = sum(t.amount for t in recent_txs)
    if daily_spent + request.amount > MAX_IMPS_DAILY_LIMIT:
        remaining = max(0.0, MAX_IMPS_DAILY_LIMIT - daily_spent)
        raise HTTPException(
            status_code=400,
            detail=f"Daily IMPS transfer limit of ₹{MAX_IMPS_DAILY_LIMIT:,.2f} exceeded. You have already transferred ₹{daily_spent:,.2f} today. Remaining daily allowance: ₹{remaining:,.2f}."
        )
        
    sender = session.exec(select(UserTable).where(UserTable.username == sender_username)).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found.")
        
    recipient = session.exec(select(UserTable).where(UserTable.username == recipient_username)).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found.")
        
    from utils import verify_credential
    def save_mpin_hash(hashed):
        sender.mpin = hashed
        session.add(sender)
        session.commit()
        
    if not verify_credential(request.mpin, sender.mpin, on_success_callback=save_mpin_hash):
        raise HTTPException(status_code=400, detail="Incorrect MPIN.")
        
    source = request.source_account.lower().strip()
    if source == "checking":
        if sender.checking_balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds in Checking account.")
        sender.checking_balance -= request.amount
    elif source == "savings":
        if sender.savings_balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds in Savings account.")
        sender.savings_balance -= request.amount
    else:
        raise HTTPException(status_code=400, detail="Invalid source account. Choose savings or checking.")
        
    recipient.savings_balance += request.amount
    
    # Save both sender and recipient
    session.add(sender)
    session.add(recipient)
    
    # Record transaction records
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Sender debit
    sender_tx = TransactionTable(
        username=sender_username,
        description=f"Transfer to {recipient.name}",
        category="Transfer",
        type="debit",
        amount=request.amount,
        date=now_str
    )
    # Recipient credit
    recipient_tx = TransactionTable(
        username=recipient_username,
        description=f"Transfer from {sender.name}",
        category="Transfer",
        type="credit",
        amount=request.amount,
        date=now_str
    )
    
    session.add(sender_tx)
    session.add(recipient_tx)
    session.commit()
    
    return {
        "success": True,
        "message": f"Successfully transferred ₹{request.amount:.2f} to {recipient.name}."
    }
