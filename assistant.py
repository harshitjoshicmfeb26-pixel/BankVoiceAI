import os
import datetime
import contextvars
from google import genai
from google.genai import types
from dotenv import load_dotenv
from sqlmodel import Session, select

from database import engine
from models import UserTable, TransactionTable, FixedDepositTable

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client if API key is provided
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# Session context tracking for Gemini synchronous functions
current_user_var = contextvars.ContextVar("current_user", default=None)

# --- Tools defined for Gemini API (Context Aware) ---

def get_fixed_deposit_details() -> str:
    """
    Fetches details of the customer's current Fixed Deposits (FD), including the principal amount,
    booking date, maturity date, interest rate, and tenure.
    
    Returns:
        A text summary of the Fixed Deposit account details.
    """
    username = current_user_var.get()
    if not username:
        return "Error: User is not authenticated."
        
    with Session(engine) as session:
        fds = session.exec(select(FixedDepositTable).where(FixedDepositTable.username == username)).all()
        if not fds:
            return "You do not have any active Fixed Deposits."
        
        fd = fds[0]
        return (
            f"You have an active Fixed Deposit (ID: {fd.id}) of amount ${fd.principal_amount:.2f} "
            f"at an interest rate of {fd.interest_rate}. The tenure is {fd.tenure}. "
            f"It was booked on {fd.booking_date} and matures on {fd.maturity_date}."
        )

def get_transaction_history(limit: int = 10) -> str:
    """
    Retrieves the customer's recent transaction history showing transaction date, amount, description, and type.
    
    Args:
        limit: The maximum number of transactions to retrieve. Defaults to 10.
    """
    username = current_user_var.get()
    if not username:
        return "Error: User is not authenticated."
        
    with Session(engine) as session:
        statement = select(TransactionTable).where(TransactionTable.username == username).order_by(TransactionTable.date.desc()).limit(limit)
        txs = session.exec(statement).all()
        
        if not txs:
            return "No transactions found in your history."
        
        result = f"Here are your last {len(txs)} transactions:\n"
        for tx in txs:
            result += f"- {tx.date}: {tx.type} of ${tx.amount:.2f} for '{tx.description}' ({tx.category})\n"
        return result

def send_money(recipient: str, amount: float, source_account: str = "savings") -> str:
    """
    Sends or transfers money to another bank customer from a specified source account.
    
    Args:
        recipient: The name or username of the person receiving the money.
        amount: The amount of money to transfer. Must be positive.
        source_account: The account to transfer from. Must be either 'savings' or 'checking'. Defaults to 'savings'.
    """
    sender = current_user_var.get()
    if not sender:
        return "Error: Sender is not authenticated."
        
    if amount <= 0:
        return "Error: Transfer amount must be greater than zero."
        
    source = source_account.lower().strip()
    if source not in ["savings", "checking"]:
        return f"Error: Invalid source account '{source_account}'. Please choose 'savings' or 'checking'."

    with Session(engine) as session:
        try:
            # Query Sender User object
            db_sender = session.exec(select(UserTable).where(UserTable.username == sender)).first()
            if not db_sender:
                return "Error: Sender profile not found in database."

            # Check Balance
            current_balance = getattr(db_sender, f"{source}_balance")
            if current_balance < amount:
                return f"Error: Insufficient funds in your {source} account. Your current balance is ${current_balance:.2f}."

            # Resolve Recipient (fuzzy match name or username)
            recipient_clean = recipient.lower().strip()
            all_users = session.exec(select(UserTable)).all()
            db_recipient = None
            for u in all_users:
                if u.username == recipient_clean or u.name.lower() == recipient_clean or recipient_clean in u.name.lower():
                    db_recipient = u
                    break

            if not db_recipient:
                return f"Error: Recipient '{recipient}' not found in Finova Bank database."
                
            if db_recipient.username == sender:
                return "Error: You cannot transfer money to yourself."

            # Update Balances
            setattr(db_sender, f"{source}_balance", current_balance - amount)
            db_recipient.savings_balance += amount  # Default incoming to savings

            # Insert transaction records
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            sender_tx = TransactionTable(
                username=sender,
                date=now_str,
                type="Debit",
                amount=amount,
                description=f"Transfer to {db_recipient.name}",
                category="Transfers"
            )
            recipient_tx = TransactionTable(
                username=db_recipient.username,
                date=now_str,
                type="Credit",
                amount=amount,
                description=f"Received from {db_sender.name}",
                category="Transfers"
            )

            session.add_all([db_sender, db_recipient, sender_tx, recipient_tx])
            session.commit()
            
            new_balance = getattr(db_sender, f"{source}_balance")
            return f"Successfully sent ${amount:.2f} to {db_recipient.name} from your {source} account. Your new {source} balance is ${new_balance:.2f}."
        except Exception as e:
            session.rollback()
            return f"Error executing transfer: {str(e)}"
