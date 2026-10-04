import re
import jwt
import datetime
import os
import logging
from typing import Optional
from fastapi import HTTPException, Header, Depends
from sqlmodel import Session, select
from models import UserTable, TransactionTable, FixedDepositTable
from database import get_db_session

# Setup logger for security events
logger = logging.getLogger("bankvoiceai.security")

def transliterate_devanagari(text: str) -> str:
    char_map = {
        'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'i', 'उ': 'u', 'ऊ': 'u', 'ऋ': 'r', 
        'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'n',
        'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
        'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
        'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
        'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'u', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
        'ॉ': 'o', 'ं': 'n', 'ः': 'h', 'ॅ': 'e', '्': ''
    }
    return "".join(char_map.get(c, c) for c in text)

def check_passphrase_similarity(registered: str, spoken: str) -> bool:
    if not registered or not spoken:
        return False
        
    # Clean and normalize strings
    reg_clean = re.sub(r"[^\w\s]", "", registered.lower()).strip()
    spk_clean = re.sub(r"[^\w\s]", "", spoken.lower()).strip()
    
    # Enforce minimum length on spoken passphrase to avoid single-word / fragment logins
    if len(spk_clean) < 6:
        return False
        
    # 1. Exact match or spoken sentence contains full registered passphrase
    # (Notice: dropped `spk_clean in reg_clean` which allowed matching single word fragments like "my")
    if reg_clean == spk_clean or reg_clean in spk_clean:
        return True
        
    # 2. Word overlap (Jaccard similarity on unique words)
    reg_words = set(reg_clean.split())
    spk_words = set(spk_clean.split())
    
    if reg_words and spk_words and len(spk_words) >= 2:
        intersection = reg_words.intersection(spk_words)
        jaccard_ratio = len(intersection) / len(reg_words)
        if jaccard_ratio >= 0.75:
            return True
            
    # 3. Character sequence similarity (difflib SequenceMatcher ratio)
    import difflib
    char_ratio = difflib.SequenceMatcher(None, reg_clean, spk_clean).ratio()
    if char_ratio >= 0.75:
        return True
        
    return False

def normalize_spoken_digits(text: str) -> str:
    word_to_digit = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }
    
    text = text.lower().strip()
    text = re.sub(r"[,\-\.\?]", " ", text)
    
    words = text.split()
    
    converted_words = []
    for w in words:
        if w in word_to_digit:
            converted_words.append(word_to_digit[w])
        else:
            converted_words.append(w)
            
    result = []
    current_digits = []
    
    for word in converted_words:
        if word.isdigit():
            current_digits.append(word)
        else:
            if current_digits:
                result.append("".join(current_digits))
                current_digits = []
            result.append(word)
    if current_digits:
        result.append("".join(current_digits))
        
    return " ".join(result)

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

def log_token_usage(agent_name: str, usage_metadata: dict):
    if not usage_metadata:
        return
    import datetime
    import json
    log_file = "token_usage.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "agent": agent_name,
        "input_tokens": usage_metadata.get("input_tokens", 0),
        "output_tokens": usage_metadata.get("output_tokens", 0),
        "total_tokens": usage_metadata.get("total_tokens", 0)
    }
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        print(f"[{timestamp}] [Token Usage] {agent_name}: Input={log_entry['input_tokens']}, Output={log_entry['output_tokens']}, Total={log_entry['total_tokens']}", flush=True)
    except Exception as e:
        print(f"Failed to write token log: {e}", flush=True)


# ==========================================
# CREDENTIAL HASHING & AUTomigration (Argon2id)
# ==========================================
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize global PasswordHasher for Argon2id
ph = PasswordHasher()

def hash_credential(plain_val: str) -> str:
    """
    Hashes a plain text credential (password, MPIN, security answer) using Argon2id.
    """
    if not plain_val:
        return ""
    return ph.hash(plain_val.strip())

def verify_credential(entered_val: str, stored_val: str, on_success_callback=None) -> bool:
    """
    Verifies an entered plain text credential against a stored value.
    Supports auto-migration from legacy plaintext values.
    
    If verification succeeds and the stored value is legacy plaintext, 
    the callback 'on_success_callback(hashed_value)' is triggered to persist the hash.
    """
    if not entered_val or not stored_val:
        return False
        
    entered_clean = entered_val.strip()
    stored_clean = stored_val.strip()
    
    # 1. Check if the stored value is an Argon2id hash
    if stored_clean.startswith("$argon2id$"):
        try:
            ph.verify(stored_clean, entered_clean)
            return True
        except VerifyMismatchError:
            return False
        except Exception as e:
            print(f"Argon2 verification error: {e}")
            return False
            
    # 2. Legacy Plaintext Fallback (Case-insensitive check for answers, case-sensitive otherwise)
    is_match = (entered_clean == stored_clean) or (entered_clean.lower() == stored_clean.lower())
    
    if is_match:
        # Auto-migrate: hash the plaintext and execute the callback to update the database
        if on_success_callback:
            try:
                hashed = ph.hash(entered_clean)
                on_success_callback(hashed)
                print("Credential automatically migrated to secure Argon2id hash.")
            except Exception as e:
                print(f"Auto-migration hash save warning: {e}")
        return True
        
    return False


# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
if not JWT_SECRET or JWT_SECRET in ["super-secret-key-for-bank-voice-ai", "your_jwt_secret_key_here"]:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: 'JWT_SECRET' (or 'SECRET_KEY') is not set or uses the insecure repository default! "
        "Please configure a strong, random JWT_SECRET in your .env file."
    )
JWT_ALGORITHM = "HS256"

def create_access_token(username: str, expires_delta_mins: int = 60) -> str:
    """
    Generates a secure, cryptographically signed JWT access token.
    """
    payload = {
        "sub": username.lower().strip(),
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_delta_mins)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(authorization: Optional[str] = Header(None), session: Session = Depends(get_db_session)) -> str:
    """
    FastAPI dependency to extract and verify the JWT access token from the Authorization header.
    Returns the authenticated username.
    """
    if not authorization:
        logger.warning("Authentication failed: Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization token.")
        
    try:
        # Expecting format "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("Authentication failed: Invalid Authorization header format")
            raise HTTPException(status_code=401, detail="Invalid authorization header format. Use 'Bearer <token>'.")
            
        token = parts[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.warning("Authentication failed: Token payload is missing subject ('sub') claim")
            raise HTTPException(status_code=401, detail="Token payload is missing subject.")
            
        # Verify user still exists in the database
        user = session.exec(select(UserTable).where(UserTable.username == username)).first()
        if not user:
            logger.warning(f"Authentication failed: User '{username}' encoded in token does not exist in DB")
            raise HTTPException(status_code=401, detail="User in token does not exist.")
            
        return username
    except jwt.ExpiredSignatureError:
        logger.warning("Authentication failed: Token signature has expired")
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Authentication failed: Invalid signature/token. Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token. Please log in again.")


