import os
import datetime
import contextvars
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Optional
from sqlmodel import Session, select

from database import engine
from models import UserTable, TransactionTable, FixedDepositTable
from utils import log_token_usage

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client if API key is provided
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# Session context tracking for Gemini synchronous functions
current_user_var = contextvars.ContextVar("current_user", default=None)
# Context variable to hold transactions returned by the last query
last_queried_transactions = contextvars.ContextVar("last_queried_transactions", default=None)

# In-memory store for pending transactions
# Key: username (str), Value: dict with keys: 'recipient_username', 'recipient_name', 'amount', 'source_account'
pending_transfers = {}

# In-memory store for chat histories
# Key: username (str), Value: list of LangChain messages
chat_histories = {}


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
            f"You have an active Fixed Deposit (ID: {fd.id}) of amount ₹{fd.principal_amount:.2f} "
            f"at an interest rate of {fd.interest_rate}. The tenure is {fd.tenure}. "
            f"It was booked on {fd.booking_date} and matures on {fd.maturity_date}."
        )

def get_transaction_history(
    limit: int = 10,
    transaction_type: Optional[str] = None,
    channel: Optional[str] = None,
    other_party: Optional[str] = None,
    target_user: Optional[str] = None
) -> str:
    """
    Retrieves transaction history showing transaction date, amount, description, and type.
    Supports querying a specific user's transactions if target_user is specified (e.g., 'alice', 'bob').
    If target_user is not specified, it defaults to the currently authenticated user.
    Supports filtering by transaction type ('Credit' or 'Debit'), channel ('Voice' or 'Web'), or a specific recipient/sender's name or username.
    
    Args:
        limit: The maximum number of transactions to retrieve. Defaults to 10.
        transaction_type: Optional filter for transaction type. Must be either 'Credit' or 'Debit' (case-insensitive).
        channel: Optional filter for channel. Must be either 'Voice' or 'Web' (case-insensitive).
        other_party: Optional filter for a specific recipient/sender name or username involved in the transaction (e.g., 'David Miller' or 'Admin'). Case-insensitive.
        target_user: Optional username of the user whose transactions are being retrieved (e.g., 'alice', 'bob', 'charlie'). If not provided, retrieves the logged-in user's transactions.
    """
    query_user = target_user.strip().lower() if target_user else current_user_var.get()
    if not query_user:
        return "Error: User is not authenticated."
        
    with Session(engine) as session:
        # Verify target user exists, fuzzy matching full name if needed
        db_user = session.exec(select(UserTable).where(UserTable.username == query_user)).first()
        if not db_user:
            all_users = session.exec(select(UserTable)).all()
            for u in all_users:
                if u.name.lower() == query_user or query_user in u.name.lower():
                    db_user = u
                    query_user = u.username
                    break
        if not db_user:
            return f"Error: User '{query_user}' was not found in the database."

        # Base query
        query = select(TransactionTable).where(TransactionTable.username == query_user)
        
        # Apply filters in database query if simple
        if transaction_type:
            ttype = transaction_type.strip().capitalize()
            query = query.where(TransactionTable.type == ttype)
            
        if channel:
            chan = channel.strip().capitalize()
            query = query.where(TransactionTable.channel == chan)
            
        # Execute query
        txs = session.exec(query.order_by(TransactionTable.date.desc())).all()
        
        # Post-filter for other_party since it matches against the transaction description (fuzzy search)
        if other_party:
            party = other_party.strip().lower()
            txs = [tx for tx in txs if party in tx.description.lower()]
            
        # Apply limit after filtering
        txs = txs[:limit]
        
        # Format the transaction list as a dictionary representation and store it in contextvar
        tx_list = [
            {
                "id": tx.id,
                "date": tx.date,
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description,
                "category": tx.category
            }
            for tx in txs
        ]
        last_queried_transactions.set(tx_list)
        
        if not txs:
            filter_desc = []
            if transaction_type: filter_desc.append(f"type '{transaction_type}'")
            if channel: filter_desc.append(f"channel '{channel}'")
            if other_party: filter_desc.append(f"involving '{other_party}'")
            filters_str = " and ".join(filter_desc)
            user_label = f"for user '{db_user.name}'" if target_user else "in your history"
            return f"No transactions found matching {filters_str} {user_label}." if filters_str else f"No transactions found {user_label}."
        
        user_label = f"for user '{db_user.name}'" if target_user else "in your history"
        table = f"Here are the last {len(txs)} transactions {user_label}:\n\n"
        table += "| Date | Description | Category | Type | Amount |\n"
        table += "| :--- | :--- | :--- | :--- | :--- |\n"
        for tx in txs:
            sign = "+" if tx.type.lower() == "credit" else "-"
            table += f"| {tx.date} | {tx.description} | {tx.category} | {tx.type} | {sign}₹{tx.amount:.2f} |\n"
        return table

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
                return f"Error: Insufficient funds in your {source} account. Your current balance is ₹{current_balance:.2f}."

            # Resolve Recipient (fuzzy match name or username)
            recipient_clean = recipient.lower().strip()
            all_users = session.exec(select(UserTable)).all()
            
            # If the recipient name contains non-ASCII characters (e.g. Devanagari Hindi/Marathi),
            # use Gemini to dynamically resolve the phonetic/translation match to a database user.
            if client and any(ord(c) > 127 for c in recipient_clean):
                user_list_str = "\n".join([f"- Username: {u.username}, Name: {u.name}" for u in all_users])
                prompt = (
                    f"You are a database entity resolution assistant. The user wants to transfer money to a person.\n"
                    f"Spoken/written recipient name: '{recipient}'\n"
                    f"List of available users in the database:\n"
                    f"{user_list_str}\n\n"
                    f"Find the database user whose username or name matches the spoken recipient name (which may be in a different language/script like Hindi, Marathi, Devanagari, or phonetic English).\n"
                    f"Respond with ONLY the exact username of the matching user. If there is no match, respond with 'None'. Do not write any other text."
                )
                try:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt
                    )
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        usage = {
                            "input_tokens": response.usage_metadata.prompt_token_count,
                            "output_tokens": response.usage_metadata.candidates_token_count,
                            "total_tokens": response.usage_metadata.total_token_count
                        }
                        log_token_usage("Phonetic Entity Resolution (send_money)", usage)
                    resolved_username = response.text.strip().lower()
                    if resolved_username != "none" and resolved_username:
                        # Extract clean username token
                        resolved_username = resolved_username.split()[-1].replace("'", "").replace('"', "")
                        recipient_clean = resolved_username
                except Exception as e:
                    print(f"Error in dynamic recipient resolution: {e}")

            # Find all matching recipients
            matching_recipients = []
            for u in all_users:
                # Check for name/username matching
                if u.username == recipient_clean or u.name.lower() == recipient_clean or recipient_clean in u.name.lower() or recipient_clean in u.username:
                    matching_recipients.append(u)

            if not matching_recipients:
                return f"Error: Recipient '{recipient}' not found in NidhiVani AI database."
                
            if len(matching_recipients) > 1:
                options_str = ", ".join([f"{u.name} (username: {u.username})" for u in matching_recipients])
                return f"Error: Multiple users found matching '{recipient}': {options_str}. Please ask the user to clarify who they want to send money to by stating their full name or username."

            db_recipient = matching_recipients[0]
            if db_recipient.username == sender:
                return "Error: You cannot transfer money to yourself."

            # Store the transaction details in pending state
            pending_transfers[sender] = {
                "recipient_username": db_recipient.username,
                "recipient_name": db_recipient.name,
                "amount": amount,
                "source_account": source,
                "attempts": 0
            }

            return f"PENDING_CONFIRMATION: A transfer of ₹{amount:.2f} to {db_recipient.name} from your {source} account is initiated. Please ask the user to state or enter their 4-digit MPIN for confirmation."
        except Exception as e:
            return f"Error preparing transfer: {str(e)}"

def get_balance() -> str:
    """
    Checks and retrieves the current bank balances for the authenticated user's accounts 
    (both savings and checking balances).
    
    Returns:
        A text summary showing the savings and checking account balances.
    """
    username = current_user_var.get()
    if not username:
        return "Error: User is not authenticated."
        
    with Session(engine) as session:
        db_user = session.exec(select(UserTable).where(UserTable.username == username)).first()
        if not db_user:
            return "Error: User profile not found in database."
        return (
            f"Your account balances are:\n"
            f"- Savings Account: ₹{db_user.savings_balance:.2f}\n"
            f"- Checking Account: ₹{db_user.checking_balance:.2f}"
        )
