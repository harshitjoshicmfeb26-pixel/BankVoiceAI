import re
from fastapi import HTTPException
from sqlmodel import Session, select
from models import UserTable, TransactionTable, FixedDepositTable

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
    
    # 1. Direct match or substring match
    if reg_clean == spk_clean or reg_clean in spk_clean or spk_clean in reg_clean:
        return True
        
    # 2. Word overlap (Jaccard similarity on unique words)
    reg_words = set(reg_clean.split())
    spk_words = set(spk_clean.split())
    
    if reg_words and spk_words:
        intersection = reg_words.intersection(spk_words)
        jaccard_ratio = len(intersection) / len(reg_words)
        if jaccard_ratio >= 0.70:
            return True
            
    # 3. Character sequence similarity (difflib SequenceMatcher ratio)
    import difflib
    char_ratio = difflib.SequenceMatcher(None, reg_clean, spk_clean).ratio()
    if char_ratio >= 0.70:
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

