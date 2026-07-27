import datetime
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from google.genai import types

from database import get_db_session
from models import UserTable, TransactionTable, FixedDepositTable
from assistant import client, current_user_var, get_fixed_deposit_details, get_transaction_history, send_money

router = APIRouter()

# --- API Request Models ---

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    voice_passphrase: str
    initial_savings: float = 1000.0
    initial_checking: float = 500.0

class VoiceLoginRequest(BaseModel):
    passphrase: str

class ChatRequest(BaseModel):
    message: str
    username: str

# --- Helper functions ---

def get_user_current_state(username: str, session: Session):
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
        
    txs = session.exec(select(TransactionTable).where(TransactionTable.username == username).order_by(TransactionTable.date.desc())).all()
    fds = session.exec(select(FixedDepositTable).where(FixedDepositTable.username == username)).all()
    
    return {
        "balances": {
            "savings": user.savings_balance,
            "checking": user.checking_balance
        },
        "transactions": [
            {"id": tx.id, "date": tx.date, "type": tx.type, "amount": tx.amount, "description": tx.description, "category": tx.category}
            for tx in txs
        ],
        "fixed_deposits": [
            {
                "id": fd.id,
                "principal_amount": fd.principal_amount,
                "interest_rate": fd.interest_rate,
                "tenure": fd.tenure,
                "booking_date": fd.booking_date,
                "maturity_date": fd.maturity_date,
                "status": fd.status
            }
            for fd in fds
        ]
    }

# --- API Router Endpoints ---

@router.post("/api/login")
async def login_endpoint(request: LoginRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if user and user.password == request.password:
        return {
            "success": True,
            "username": username,
            "name": user.name
        }
    raise HTTPException(status_code=401, detail="Invalid username or password.")

@router.post("/api/register")
async def register_endpoint(request: RegisterRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
    
    user_exists = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username already exists.")
        
    try:
        new_user = UserTable(
            username=username,
            password=request.password,
            name=request.name,
            voice_passphrase=request.voice_passphrase,
            savings_balance=request.initial_savings,
            checking_balance=request.initial_checking
        )
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        tx_savings = TransactionTable(
            username=username,
            date=now_str,
            type="Credit",
            amount=request.initial_savings,
            description="Initial Savings Deposit",
            category="Income"
        )
        tx_checking = TransactionTable(
            username=username,
            date=now_str,
            type="Credit",
            amount=request.initial_checking,
            description="Initial Checking Deposit",
            category="Income"
        )
        
        session.add_all([new_user, tx_savings, tx_checking])
        session.commit()
        
        return {
            "success": True,
            "username": username,
            "name": request.name
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database registration error: {str(e)}")

@router.post("/api/voice-login")
async def voice_login_endpoint(request: VoiceLoginRequest, session: Session = Depends(get_db_session)):
    spoken = request.passphrase.lower().strip().replace(".", "").replace("!", "").replace(",", "")
    
    all_users = session.exec(select(UserTable)).all()
    for user in all_users:
        registered_phrase = user.voice_passphrase.lower().strip().replace(".", "").replace("!", "").replace(",", "")
        
        if registered_phrase and (registered_phrase in spoken or spoken in registered_phrase):
            return {
                "success": True,
                "username": user.username,
                "name": user.name
            }
            
    return {
        "success": False,
        "message": f"Voice phrase not matched."
    }

@router.get("/api/state")
async def state_endpoint(username: str, session: Session = Depends(get_db_session)):
    username = username.lower().strip()
    try:
        return get_user_current_state(username, session)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/chat")
async def chat_endpoint(request: ChatRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    db_user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User session not found.")
        
    current_user_var.set(username)

    if not client:
        user_msg = request.message.lower()
        response_text = ""
        
        if "send" in user_msg or "transfer" in user_msg:
            amount_match = re.search(r"(\d+(\.\d+)?)", user_msg)
            amount = float(amount_match.group(1)) if amount_match else 50.0
            
            try:
                db_user.savings_balance -= amount
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                sim_tx = TransactionTable(
                    username=username,
                    date=now_str,
                    type="Debit",
                    amount=amount,
                    description="Simulated voice transfer",
                    category="Transfers"
                )
                session.add_all([db_user, sim_tx])
                session.commit()
                response_text = f"[Simulation Mode] I parsed a transfer request. Successfully sent ${amount:.2f} to your beneficiary from your savings account. Configure GEMINI_API_KEY in your .env file to enable actual AI tool execution!"
            except Exception as e:
                session.rollback()
                response_text = f"[Simulation Mode] Failed simulated transfer: {str(e)}"
                
        elif "transaction" in user_msg or "history" in user_msg or "statement" in user_msg:
            tx_count = session.exec(select(TransactionTable).where(TransactionTable.username == username)).all()
            response_text = f"[Simulation Mode] Displaying transaction history. You have {len(tx_count)} transactions in database. Set your GEMINI_API_KEY to search specific counts."
        elif "fd" in user_msg or "fixed deposit" in user_msg or "tenure" in user_msg:
            fds = session.exec(select(FixedDepositTable).where(FixedDepositTable.username == username)).all()
            if fds:
                fd = fds[0]
                response_text = f"[Simulation Mode] Your fixed deposit {fd.id} has a tenure of {fd.tenure} and matures on {fd.maturity_date}."
            else:
                response_text = "[Simulation Mode] You do not have any active Fixed Deposits in database. Configure GEMINI_API_KEY to create one."
        else:
            response_text = f"Welcome {db_user.name}! [Simulation Mode] Configure GEMINI_API_KEY to enable conversational voice controls."
            
        return {
            "response": response_text,
            "state": get_user_current_state(username, session)
        }

    try:
        system_instruction = (
            f"You are a helpful, secure, and concise voice banking assistant for 'Finova Bank'. "
            f"You are assisting logged in user '{db_user.name}'. "
            f"Use the tools provided to access their accounts, transactions, or fixed deposits. "
            f"If they ask to send money, use the send_money tool. Always verify if they specify checking/savings source; default to savings if unspecified. "
            f"If they ask for transaction history, use the get_transaction_history tool. "
            f"If they ask about fixed deposits, use the get_fixed_deposit_details tool. "
            f"Keep your responses friendly, polite, and very short, optimized for voice text-to-speech."
        )

        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[get_fixed_deposit_details, get_transaction_history, send_money],
            )
        )
        
        # Expire session models to fetch updated balance state from DB tool adjustments
        session.expire_all()
        return {
            "response": response.text,
            "state": get_user_current_state(username, session)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
