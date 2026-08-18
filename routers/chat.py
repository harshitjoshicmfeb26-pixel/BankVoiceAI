import datetime
import re
import os
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from langchain_core.messages import HumanMessage, AIMessage

from database import get_db_session
from models import UserTable, TransactionTable, FixedDepositTable
from assistant import (
    client,
    current_user_var,
    pending_transfers,
    last_queried_transactions,
    chat_histories
)
from agents_graph import agents_graph
from utils import (
    transliterate_devanagari,
    normalize_spoken_digits,
    get_user_current_state
)
from translations import (
    get_translated_message,
    get_simulation_message
)
from schemas import ChatRequest

router = APIRouter()

def prune_chat_history(messages, max_messages=20):
    if len(messages) <= max_messages:
        return messages
    cutoff = len(messages) - max_messages
    for i in range(cutoff, len(messages)):
        if isinstance(messages[i], HumanMessage):
            return messages[i:]
    return messages[cutoff:]

def add_to_history(username: str, user_message: str, assistant_response: str):
    history = chat_histories.setdefault(username, [])
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=assistant_response))
    chat_histories[username] = prune_chat_history(history)

@router.post("/api/chat")
async def chat_endpoint(request: ChatRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    db_user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User session not found.")
        
    current_user_var.set(username)

    # Check if there is a pending transfer for this user
    if username in pending_transfers:
        user_msg = request.message.lower().strip()
        user_msg = normalize_spoken_digits(user_msg)
        
        resp = None
        # Check if the user wants to cancel the transfer
        if any(cancel_word in user_msg for cancel_word in ["cancel", "abort", "stop", "no"]):
            del pending_transfers[username]
            resp = {
                "response": get_translated_message("cancel_success", request.language),
                "state": get_user_current_state(username, session),
                "pending_transfer": False
            }
            
        else:
            transfer_info = pending_transfers[username]
            if transfer_info.get("pending_recipient_resolution"):
                possible = transfer_info["possible_recipients"]
                matched_recipient = None
                msg_clean = transliterate_devanagari(user_msg)
                
                # 1. Exact full name match
                for pr in possible:
                    p_name_lower = pr["name"].lower()
                    p_name_trans = transliterate_devanagari(p_name_lower)
                    if msg_clean == p_name_lower or msg_clean == p_name_trans:
                        matched_recipient = pr
                        break
                
                # 2. Exact username match
                if not matched_recipient:
                    for pr in possible:
                        if msg_clean == pr["username"].lower():
                            matched_recipient = pr
                            break
                
                # 3. Substring full name match
                if not matched_recipient:
                    for pr in possible:
                        p_name_trans = transliterate_devanagari(pr["name"].lower())
                        if p_name_trans in msg_clean:
                            matched_recipient = pr
                            break

                # 4. Whole-word username match
                if not matched_recipient:
                    for pr in possible:
                        p_uname = pr["username"].lower()
                        if re.search(rf"\b{re.escape(p_uname)}\b", msg_clean):
                            matched_recipient = pr
                            break
                            
                # 5. First name match
                if not matched_recipient:
                    for pr in possible:
                        first_name = pr["name"].split()[0].lower()
                        first_name_trans = transliterate_devanagari(first_name)
                        if first_name_trans in msg_clean:
                            matched_recipient = pr
                            break
                
                if matched_recipient:
                    transfer_info["recipient_username"] = matched_recipient["username"]
                    transfer_info["recipient_name"] = matched_recipient["name"]
                    del transfer_info["pending_recipient_resolution"]
                    del transfer_info["possible_recipients"]
                    
                    response_text = get_translated_message("pending_transfer_prompt", request.language, amount=transfer_info['amount'], recipient_name=matched_recipient['name'])
                    resp = {
                        "response": response_text,
                        "state": get_user_current_state(username, session),
                        "pending_transfer": True
                    }
                else:
                    options_str = " or ".join([f"{pr['name']} ({pr['username']})" for pr in possible])
                    if "hi" in (request.language or "").lower():
                        prompt_msg = f"कृपया स्पष्ट करें कि आप किसे पैसे भेजना चाहते हैं: {options_str}?"
                    elif "mr" in (request.language or "").lower():
                        prompt_msg = f"कृपया स्पष्ट करा की तुम्हाला कोणाला पैसे पाठवायचे आहेत: {options_str}?"
                    else:
                        prompt_msg = f"I found multiple matches. Did you mean {options_str}? Please specify the recipient's name or username."
                        
                    resp = {
                        "response": prompt_msg,
                        "state": get_user_current_state(username, session),
                        "pending_transfer": True
                    }

            else:
                # Check if the user entered/said a 4-digit MPIN
                mpin_match = re.search(r"\b(\d{4})\b", user_msg)
                if mpin_match:
                    entered_mpin = mpin_match.group(1)
                    
                    # Verify MPIN
                    if entered_mpin == db_user.mpin:
                        # MPIN is correct! Complete the transfer.
                        tx_info = pending_transfers[username]
                        del pending_transfers[username]
                        
                        recipient_uname = tx_info["recipient_username"]
                        recipient_name = tx_info["recipient_name"]
                        amount = tx_info["amount"]
                        source = tx_info["source_account"]
                        
                        try:
                            db_sender = db_user
                            db_recipient = session.exec(select(UserTable).where(UserTable.username == recipient_uname)).first()
                            
                            if not db_recipient:
                                raise Exception("Recipient not found during execution.")
                                
                            # Double-check balance
                            sender_balance = getattr(db_sender, f"{source}_balance")
                            if sender_balance < amount:
                                raise Exception(f"Insufficient funds in your {source} account. Current balance is ₹{sender_balance:.2f}.")
                            
                            # Update balances
                            setattr(db_sender, f"{source}_balance", sender_balance - amount)
                            db_recipient.savings_balance += amount
                            
                            # Insert transaction records
                            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            sender_tx = TransactionTable(
                                username=username,
                                date=now_str,
                                type="Debit",
                                amount=amount,
                                description=f"Transfer to {recipient_name} (via Voice)",
                                category="Transfers",
                                channel="Voice"
                            )
                            recipient_tx = TransactionTable(
                                username=recipient_uname,
                                date=now_str,
                                type="Credit",
                                amount=amount,
                                description=f"Received from {db_sender.name} (via Voice)",
                                category="Transfers",
                                channel="Voice"
                            )
                            
                            session.add_all([db_sender, db_recipient, sender_tx, recipient_tx])
                            session.commit()
                            
                            # Force session refresh
                            session.expire_all()
                            
                            new_balance = getattr(db_sender, f"{source}_balance")
                            response_text = get_translated_message("transfer_success", request.language, amount=amount, recipient_name=recipient_name, source=source, new_balance=new_balance)
                            
                        except Exception as e:
                            session.rollback()
                            response_text = get_translated_message("transfer_failed", request.language, error=str(e))
                            
                        resp = {
                            "response": response_text,
                            "state": get_user_current_state(username, session),
                            "pending_transfer": False
                        }
                    else:
                        # Incorrect MPIN
                        tx_info = pending_transfers[username]
                        attempts = tx_info.get("attempts", 0) + 1
                        tx_info["attempts"] = attempts
                        
                        if attempts >= 3:
                            # Cancel the transfer and signal logout
                            del pending_transfers[username]
                            resp = {
                                "response": get_translated_message("too_many_attempts", request.language),
                                "state": get_user_current_state(username, session),
                                "pending_transfer": False,
                                "logout": True
                            }
                        else:
                            remaining_attempts = 3 - attempts
                            attempt_word = "attempt" if remaining_attempts == 1 else "attempts"
                            if "hi" in (request.language or "").lower():
                                attempt_word = "प्रयास"
                            elif "mr" in (request.language or "").lower():
                                attempt_word = "प्रयत्न"
                                
                            resp = {
                                "response": get_translated_message("incorrect_mpin", request.language, remaining_attempts=remaining_attempts, attempt_word=attempt_word),
                                "state": get_user_current_state(username, session),
                                "pending_transfer": True
                            }
                else:
                    # User sent a message but did not provide a 4-digit MPIN or cancel
                    transfer_details = pending_transfers[username]
                    resp = {
                        "response": get_translated_message("pending_transfer_prompt", request.language, amount=transfer_details['amount'], recipient_name=transfer_details['recipient_name']),
                        "state": get_user_current_state(username, session),
                        "pending_transfer": True
                    }
        if resp:
            add_to_history(username, request.message, resp["response"])
            return resp

    fallback_to_simulation = False
    api_error_msg = ""

    if client:
        try:
            lang_names = {
                "en-in": "English", "en-us": "English",
                "hi-in": "Hindi",
                "mr-in": "Marathi"
            }
            lang_name = lang_names.get(request.language.lower() if request.language else "en-in", "English")

            # Reset last queried transactions before generation
            last_queried_transactions.set(None)

            # Retrieve and update chat history
            history = chat_histories.setdefault(username, [])
            history.append(HumanMessage(content=request.message))
            history = prune_chat_history(history)

            # Invoke LangGraph multi-agent system
            inputs = {
                "messages": history,
                "db_user_name": db_user.name,
                "language_name": lang_name
            }
            result = agents_graph.invoke(inputs)
            
            raw_content = result["messages"][-1].content
            if isinstance(raw_content, list):
                response_text = "".join([part if isinstance(part, str) else part.get("text", "") if isinstance(part, dict) else str(part) for part in raw_content])
            else:
                response_text = str(raw_content)
            active_agent = result["active_agent_name"]

            # Save the full updated messages list back to history
            chat_histories[username] = list(result["messages"])

            # Retrieve the queried transactions from the tool call, if any
            queried_txs = last_queried_transactions.get()

            # Expire session models to fetch updated balance state from DB tool adjustments
            session.expire_all()
            return {
                "response": response_text,
                "state": get_user_current_state(username, session),
                "pending_transfer": username in pending_transfers,
                "queried_transactions": queried_txs,
                "active_agent": active_agent
            }
        except Exception as e:
            fallback_to_simulation = True
            print(f"Gemini API Quota Exceeded or Error: {e}", flush=True)
            api_error_msg = ""

    if not client or fallback_to_simulation:
        user_msg = request.message.lower()
        response_text = ""
        
        if "send" in user_msg or "transfer" in user_msg or "भेज" in user_msg or "हस्तांतरण" in user_msg or "पाठव" in user_msg or "पैसे" in user_msg:
            amount_match = re.search(r"(\d+(\.\d+)?)", user_msg)
            amount = float(amount_match.group(1)) if amount_match else 50.0
            
            source = "checking" if ("checking" in user_msg or "चालू" in user_msg) else "savings"
            
            # Extract recipient dynamically using phonetic transliteration and fuzzy matching
            matching_users = []
            import difflib
            
            # Translating message to phonetic English to normalize Hindi/Marathi/English scripts
            user_msg_trans = transliterate_devanagari(user_msg)
            all_users = session.exec(select(UserTable)).all()
            
            # Extract candidate words from the transliterated message
            words = re.findall(r"\b\w+\b", user_msg_trans)
            
            # Check exact substring matches in the transliterated sentence first (highest confidence)
            for u in all_users:
                uname = u.username.lower()
                fullname = u.name.lower()
                first_name = fullname.split()[0]
                
                # Transliterate full name in case they exist in database as Devanagari
                fullname_trans = transliterate_devanagari(fullname)
                first_name_trans = transliterate_devanagari(first_name)
                
                if (uname in user_msg_trans or 
                    first_name_trans in user_msg_trans or 
                    fullname_trans in user_msg_trans):
                    if u not in matching_users:
                        matching_users.append(u)
            
            # If no match found via exact substrings, check fuzzy word matching using SequenceMatcher (cutoff 0.75)
            if not matching_users:
                for u in all_users:
                    uname = u.username.lower()
                    fullname = u.name.lower()
                    first_name = fullname.split()[0]
                    
                    fullname_trans = transliterate_devanagari(fullname)
                    first_name_trans = transliterate_devanagari(first_name)
                    
                    for w in words:
                        ratio1 = difflib.SequenceMatcher(None, w, uname).ratio()
                        ratio2 = difflib.SequenceMatcher(None, w, first_name_trans).ratio()
                        max_ratio = max(ratio1, ratio2)
                        
                        if max_ratio > 0.75:
                            if u not in matching_users:
                                matching_users.append(u)

            # Exclude the sender themselves
            matching_users = [u for u in matching_users if u.username != username]
            
            if not matching_users:
                err_msgs = {
                    "en-in": "Error: Could not identify a valid transfer recipient. Please specify the name clearly (e.g. 'Send to Bob' or 'बॉब को पैसे भेजें').",
                    "hi-in": "त्रुटि: मान्य प्राप्तकर्ता की पहचान नहीं हो सकी। कृपया नाम स्पष्ट रूप से बताएं (जैसे 'बॉब को भेजें')।",
                    "mr-in": "त्रुटि: वैध प्राप्तकर्ता ओळखता आला नाही. कृपया नाव स्पष्टपणे सांगा (उदा. 'बॉबला पाठवा')."
                }
                lang_key = (request.language or "en-in").lower().strip()
                err_msg = err_msgs.get(lang_key if lang_key in ["hi-in", "mr-in"] else "en-in")
                return {
                    "response": api_error_msg + err_msg,
                    "state": get_user_current_state(username, session),
                    "pending_transfer": False
                }

            if len(matching_users) > 1:
                # Put in pending state with resolution flag
                pending_transfers[username] = {
                    "pending_recipient_resolution": True,
                    "amount": amount,
                    "source_account": source,
                    "possible_recipients": [{"username": u.username, "name": u.name} for u in matching_users],
                    "attempts": 0
                }
                
                options_str = " or ".join([f"{u.name} ({u.username})" for u in matching_users])
                if "hi" in (request.language or "").lower():
                    response_text = api_error_msg + f"[सिमुलेशन मोड] मुझे एक से अधिक प्राप्तकर्ता मिले। क्या आपका मतलब {options_str} से था? कृपया स्पष्ट करें।"
                elif "mr" in (request.language or "").lower():
                    response_text = api_error_msg + f"[सिम्युलेशन मोड] मला एकापेक्षा जास्त प्राप्तकर्ते आढळले. तुम्हाला {options_str} ला पैसे पाठवायचे आहेत का? कृपया स्पष्ट करा."
                else:
                    response_text = api_error_msg + f"[Simulation Mode] I found multiple matching recipients: {options_str}. Whom did you want to send money to? Please specify their name or username."
            else:
                db_recipient = matching_users[0]
                
                # Put in pending state
                pending_transfers[username] = {
                    "recipient_username": db_recipient.username,
                    "recipient_name": db_recipient.name,
                    "amount": amount,
                    "source_account": source,
                    "attempts": 0
                }
                
                response_text = api_error_msg + get_simulation_message("transfer_pending", request.language, amount=amount, recipient_name=db_recipient.name, source=source)
                
        elif "transaction" in user_msg or "history" in user_msg or "statement" in user_msg or "लेन" in user_msg or "इतिहास" in user_msg or "व्यवहार" in user_msg:
            # Parse filters from user message for simulation fallback
            filter_type = None
            filter_channel = None
            filter_party = None
            
            msg_lower = user_msg.lower()
            
            # 1. Detect Type
            if any(w in msg_lower for w in ["credit", "received", "credited", "जमा", "क्रेडिट", "मिळाले"]):
                filter_type = "Credit"
            elif any(w in msg_lower for w in ["debit", "sent", "debited", "transfer", "निकासी", "डेबिट", "पाठवले", "खर्च"]):
                filter_type = "Debit"
                
            # 2. Detect Channel
            if any(w in msg_lower for w in ["voice", "speak", "speech", "आवाज", "व्हॉइस", "बोलून"]):
                filter_channel = "Voice"
            elif any(w in msg_lower for w in ["web", "online", "वेब", "ऑनलाईन"]):
                filter_channel = "Web"
                
            # Detect target user (whose transactions to query)
            target_username = username  # default to current logged in user
            target_user_obj = db_user
            
            all_users = session.exec(select(UserTable)).all()
            for u in all_users:
                # Check if username or full name is mentioned in the query
                if u.username in msg_lower or u.name.lower() in msg_lower:
                    # Look for specific target indicators
                    target_pattern = rf"\b(of|for|belonging\s+to|list\s+of|list\s+for|history\s+of|history\s+for|account\s+of)\s+{re.escape(u.username)}\b"
                    target_name_pattern = rf"\b(of|for|belonging\s+to|list\s+of|list\s+for|history\s+of|history\s+for|account\s+of)\s+{re.escape(u.name.lower())}\b"
                    possessive_pattern = rf"\b{re.escape(u.username)}['’]s\b"
                    possessive_name_pattern = rf"\b{re.escape(u.name.lower())}['’]s\b"
                    
                    if (re.search(target_pattern, msg_lower) or 
                        re.search(target_name_pattern, msg_lower) or 
                        re.search(possessive_pattern, msg_lower) or 
                        re.search(possessive_name_pattern, msg_lower) or
                        re.search(rf"\b{re.escape(u.username)}\b\s+(transactions|history|ledger)", msg_lower) or
                        re.search(rf"\b{re.escape(u.name.lower())}\b\s+(transactions|history|ledger)", msg_lower)):
                        target_username = u.username
                        target_user_obj = u
                        break

            # 3. Detect Other Party (only if it is not the target user we are querying)
            for u in all_users:
                if u.username != target_username and (u.username in msg_lower or u.name.lower() in msg_lower):
                    filter_party = u.name.lower()
                    break
            
            # Query and filter
            query = select(TransactionTable).where(TransactionTable.username == target_username)
            if filter_type:
                query = query.where(TransactionTable.type == filter_type)
            if filter_channel:
                query = query.where(TransactionTable.channel == filter_channel)
                
            txs = session.exec(query.order_by(TransactionTable.date.desc())).all()
            
            if filter_party:
                txs = [tx for tx in txs if filter_party in tx.description.lower()]
                
            txs = txs[:10]
            
            queried_txs = []
            if not txs:
                filter_desc = []
                if filter_type: filter_desc.append(f"type '{filter_type}'")
                if filter_channel: filter_desc.append(f"channel '{filter_channel}'")
                if filter_party: filter_desc.append(f"involving '{filter_party}'")
                filters_str = " and ".join(filter_desc)
                user_label = f"for user '{target_user_obj.name}'" if target_username != username else "in your history"
                response_text = api_error_msg + (f"No transactions found matching {filters_str} {user_label}." if filters_str else f"No transactions found {user_label}.")
            else:
                user_label = f"for user '{target_user_obj.name}'" if target_username != username else "in your history"
                table = api_error_msg + f"[Simulation Mode] Here are the last {len(txs)} transactions {user_label}:\n\n| Date | Description | Category | Type | Amount |\n| :--- | :--- | :--- | :--- | :--- |\n"
                for tx in txs:
                    sign = "+" if tx.type.lower() == "credit" else "-"
                    table += f"| {tx.date} | {tx.description} | {tx.category} | {tx.type} | {sign}₹{tx.amount:.2f} |\n"
                    queried_txs.append({
                        "id": tx.id,
                        "date": tx.date,
                        "type": tx.type,
                        "amount": tx.amount,
                        "description": tx.description,
                        "category": tx.category
                    })
                response_text = table
        elif "balance" in user_msg or "bal" in user_msg or "बैलेंस" in user_msg or "शेष" in user_msg or "शिल्लक" in user_msg:
            response_text = api_error_msg + get_simulation_message("balance_details", request.language, savings_balance=db_user.savings_balance, checking_balance=db_user.checking_balance)
        elif "fd" in user_msg or "fixed deposit" in user_msg or "tenure" in user_msg or "सावधि" in user_msg or "मुदत" in user_msg:
            fds = session.exec(select(FixedDepositTable).where(FixedDepositTable.username == username)).all()
            if fds:
                fd = fds[0]
                response_text = api_error_msg + get_simulation_message("fd_details", request.language, id=fd.id, tenure=fd.tenure, maturity_date=fd.maturity_date)
            else:
                response_text = api_error_msg + get_simulation_message("no_fds", request.language)
        else:
            response_text = api_error_msg + get_simulation_message("default_welcome", request.language, name=db_user.name)
            
        is_tx_query = "transaction" in user_msg or "history" in user_msg or "statement" in user_msg or "लेन" in user_msg or "इतिहास" in user_msg or "व्यवहार" in user_msg
        
        # Determine simulation agent
        if "send" in user_msg or "transfer" in user_msg or "balance" in user_msg or "account" in user_msg or "खाता" in user_msg or "खाते" in user_msg or "savings" in user_msg or "checking" in user_msg or is_tx_query:
            sim_agent = "Simulation (Account Specialist)"
        elif "fd" in user_msg or "fixed deposit" in user_msg or "tenure" in user_msg or "सावधि" in user_msg or "मुदत" in user_msg:
            sim_agent = "Simulation (Fixed Deposit Specialist)"
        else:
            sim_agent = "Simulation (Support Specialist)"

        resp = {
            "response": response_text,
            "state": get_user_current_state(username, session),
            "pending_transfer": username in pending_transfers,
            "queried_transactions": queried_txs if is_tx_query else None,
            "active_agent": sim_agent
        }
        add_to_history(username, request.message, resp["response"])
        return resp
