import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from database import get_db_session
from models import UserTable, TransactionTable
from schemas import DirectPaymentRequest

router = APIRouter()

@router.post("/api/payments/transfer")
async def direct_transfer_endpoint(request: DirectPaymentRequest, session: Session = Depends(get_db_session)):
    sender_username = request.username.lower().strip()
    recipient_username = request.recipient_username.lower().strip()
    
    if sender_username == recipient_username:
        raise HTTPException(status_code=400, detail="Cannot transfer money to yourself.")
        
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive.")
        
    sender = session.exec(select(UserTable).where(UserTable.username == sender_username)).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found.")
        
    recipient = session.exec(select(UserTable).where(UserTable.username == recipient_username)).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found.")
        
    if sender.mpin != request.mpin:
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
