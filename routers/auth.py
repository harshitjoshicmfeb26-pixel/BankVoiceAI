import os
import re
import base64
import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from database import get_db_session
from models import UserTable, TransactionTable
from assistant import chat_histories, client
from google.genai import types
from utils import check_passphrase_similarity, get_current_user, create_access_token
from schemas import (
    LoginRequest,
    RegisterRequest,
    VoiceLoginRequest,
    ResetPasswordRequest,
    ResetVoiceRequest,
    FaceLoginRequest,
    ResetFaceRequest
)

router = APIRouter()

# In-memory rate limiter for voice login attempts: username -> list of timestamp floats
voice_login_attempts = {}


@router.post("/api/login")
async def login_endpoint(request: LoginRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    
    from utils import verify_credential
    def save_pwd_hash(hashed):
        user.password = hashed
        session.add(user)
        session.commit()
        
    if user and verify_credential(request.password, user.password, on_success_callback=save_pwd_hash):
        chat_histories[username] = []
        from utils import create_access_token
        token = create_access_token(username)
        return {
            "success": True,
            "token": token,
            "username": username,
            "name": user.name
        }
    raise HTTPException(status_code=401, detail="Invalid username or password.")

@router.post("/api/register")
async def register_endpoint(request: RegisterRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
    
    # Validate MPIN is exactly 4 digits
    if not request.mpin or not re.match(r"^\d{4}$", request.mpin):
        raise HTTPException(status_code=400, detail="MPIN must be exactly a 4-digit number.")
        
    if not request.security_question or not request.security_question.strip():
        raise HTTPException(status_code=400, detail="Security question is required.")
        
    if not request.security_answer or not request.security_answer.strip():
        raise HTTPException(status_code=400, detail="Security answer is required.")
    
    user_exists = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username already exists.")
        
    from utils import hash_credential
    try:
        new_user = UserTable(
            username=username,
            password=hash_credential(request.password),
            name=request.name,
            voice_passphrase=request.voice_passphrase,
            mpin=hash_credential(request.mpin),
            savings_balance=request.initial_savings,
            checking_balance=request.initial_checking,
            security_question=request.security_question.strip(),
            security_answer=hash_credential(request.security_answer.strip()),
            face_image=request.face_image_base64
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
        session.add(new_user)
        session.flush()
        session.add_all([tx_savings, tx_checking])
        session.commit()
        
        # Save voice print if provided
        if request.voice_audio_base64:
            os.makedirs("voices", exist_ok=True)
            ext = "webm"
            if request.voice_audio_mime:
                if "wav" in request.voice_audio_mime:
                    ext = "wav"
                elif "ogg" in request.voice_audio_mime:
                    ext = "ogg"
                elif "mp4" in request.voice_audio_mime:
                    ext = "mp4"
            filepath = f"voices/{username}_enroll.{ext}"
            audio_bytes = base64.b64decode(request.voice_audio_base64)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
        
        token = create_access_token(username)
        return {
            "success": True,
            "token": token,
            "username": username,
            "name": request.name
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database registration error: {str(e)}")

@router.post("/api/voice-login")
async def voice_login_endpoint(request: VoiceLoginRequest, session: Session = Depends(get_db_session)):
    spoken = request.passphrase.lower().strip()
    
    if not request.username or not request.username.strip():
        return {
            "success": False,
            "message": "Please enter your username to log in with voice."
        }
        
    username_clean = request.username.lower().strip()
    now_ts = datetime.datetime.now().timestamp()
    
    # Rate limit check: max 5 failed attempts per 5-minute rolling window
    recent_attempts = [t for t in voice_login_attempts.get(username_clean, []) if now_ts - t < 300]
    voice_login_attempts[username_clean] = recent_attempts
    if len(recent_attempts) >= 5:
        return {
            "success": False,
            "message": "Too many failed voice login attempts. Please wait 5 minutes before trying again."
        }
        
    # Minimum spoken length validation
    if len(spoken) < 6:
        voice_login_attempts[username_clean].append(now_ts)
        return {
            "success": False,
            "message": "Spoken passphrase is too short. Please speak your full registered passphrase."
        }
        
    user = session.exec(select(UserTable).where(UserTable.username == username_clean)).first()
    if not user:
        voice_login_attempts[username_clean].append(now_ts)
        return {
            "success": False,
            "message": "User not found."
        }
        
    if not user.voice_passphrase or not check_passphrase_similarity(user.voice_passphrase, spoken):
        voice_login_attempts[username_clean].append(now_ts)
        return {
            "success": False,
            "message": "Voice passphrase not matched."
        }
        
    # Clear rate limit attempts upon successful verification
    voice_login_attempts.pop(username_clean, None)
    matched_user = user
    username = matched_user.username
    
    # Bypassing voice biometric verification as requested.
    # We rely on passphrase similarity match alone.
    print(f"Bypassing voice biometric verification for '{username}' (passphrase matched).", flush=True)
        
    chat_histories[username] = []
    from utils import create_access_token
    token = create_access_token(username)
    return {
        "success": True,
        "token": token,
        "username": username,
        "name": matched_user.name,
        "message": "Voice verified successfully!"
    }

@router.get("/api/forgot-password/get-question")
async def get_security_question_endpoint(username: str, session: Session = Depends(get_db_session)):
    username = username.lower().strip()
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    question = user.security_question
    if not question:
        # Fallback security question mapping for legacy seeded users
        fallbacks = {
            "alice": "What is your favorite pet's name?",
            "bob": "In which city were you born?",
            "charlie": "What is your favorite book?",
            "david": "What was the name of your first school?",
            "emma": "What is your mother's maiden name?"
        }
        question = fallbacks.get(username)
        
    if not question:
        raise HTTPException(status_code=400, detail="No security question configured for this account.")
        
    return {"success": True, "question": question}

@router.post("/api/forgot-password/reset")
async def reset_password_endpoint(request: ResetPasswordRequest, session: Session = Depends(get_db_session)):
    username = request.username.lower().strip()
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    from utils import verify_credential, hash_credential
    db_ans = user.security_answer
        
    def save_ans_hash(hashed):
        user.security_answer = hashed
        session.add(user)
        session.commit()
        
    if not db_ans or not verify_credential(request.security_answer, db_ans, on_success_callback=save_ans_hash):
        raise HTTPException(status_code=400, detail="Incorrect security answer.")
        
    user.password = hash_credential(request.new_password)
    session.add(user)
    session.commit()
    
    return {"success": True, "message": "Password reset successfully."}

@router.post("/api/settings/reset-voice")
async def reset_voice_endpoint(
    request: ResetVoiceRequest, 
    session: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    username = request.username.lower().strip()
    if username != current_user:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify other users' settings.")
        
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    from utils import verify_credential
    db_ans = user.security_answer
    db_mpin = user.mpin
        
    def save_ans_hash(hashed):
        user.security_answer = hashed
        session.add(user)
        session.commit()
        
    def save_mpin_hash(hashed):
        user.mpin = hashed
        session.add(user)
        session.commit()
        
    if not db_ans or not verify_credential(request.security_answer, db_ans, on_success_callback=save_ans_hash):
        raise HTTPException(status_code=400, detail="Incorrect security answer.")
        
    if not db_mpin or not verify_credential(request.mpin, db_mpin, on_success_callback=save_mpin_hash):
        raise HTTPException(status_code=400, detail="Incorrect MPIN.")
        
    user.voice_passphrase = request.new_voice_phrase.strip()
    session.add(user)
    session.commit()
    
    # Save new voice print if provided
    if request.voice_audio_base64:
        os.makedirs("voices", exist_ok=True)
        ext = "webm"
        if request.voice_audio_mime:
            if "wav" in request.voice_audio_mime:
                ext = "wav"
            elif "ogg" in request.voice_audio_mime:
                ext = "ogg"
            elif "mp4" in request.voice_audio_mime:
                ext = "mp4"
        filepath = f"voices/{username}_enroll.{ext}"
        audio_bytes = base64.b64decode(request.voice_audio_base64)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
            
    return {"success": True, "message": "Voice phrase reset successfully."}

face_analyzer = None

def get_face_analyzer():
    global face_analyzer
    if face_analyzer is None:
        from inference import FaceAnalysis
        face_analyzer = FaceAnalysis(device='cpu')
    return face_analyzer


@router.post("/api/face-login")
async def face_login_endpoint(request: FaceLoginRequest, session: Session = Depends(get_db_session)):
    import io
    import base64
    from PIL import Image
    
    try:
        live_bytes = base64.b64decode(request.face_image_base64)
        live_img = Image.open(io.BytesIO(live_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid live face scan image: {str(e)}")
        
    try:
        analyzer = get_face_analyzer()
    except Exception as e:
        print(f"Error loading local FaceAnalysis model: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Failed to load face analysis model: {str(e)}")
        
    username_clean = request.username.lower().strip() if request.username else None
    
    if username_clean:
        # 1:1 Matching
        user = session.exec(select(UserTable).where(UserTable.username == username_clean)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        if not user.face_image:
            raise HTTPException(status_code=400, detail="No face scan enrolled for this user.")
            
        try:
            enrolled_bytes = base64.b64decode(user.face_image)
            enrolled_img = Image.open(io.BytesIO(enrolled_bytes)).convert("RGB")
            
            similarity, is_same = analyzer.compare(enrolled_img, live_img, threshold=0.35)
            print(f"1:1 local match similarity for '{username_clean}': {similarity:.4f} (match: {is_same})", flush=True)
        except Exception as e:
            print(f"Local face match error: {e}", flush=True)
            raise HTTPException(status_code=500, detail=f"Local face recognition error: {str(e)}")
            
        if is_same:
            chat_histories[username_clean] = []
            token = create_access_token(username_clean)
            return {
                "success": True,
                "token": token,
                "username": username_clean,
                "name": user.name,
                "message": "Face verified successfully!"
            }
        else:
            raise HTTPException(status_code=401, detail=f"Face recognition match failed. (Similarity: {similarity:.4f}, threshold: 0.35)")
            
    else:
        # 1:N Identification
        users_with_face = session.exec(select(UserTable).where(UserTable.face_image != None)).all()
        if not users_with_face:
            raise HTTPException(status_code=400, detail="No enrolled face scans found in database.")
            
        best_similarity = -1.0
        best_user = None
        all_similarities = {}
        
        for u in users_with_face:
            try:
                enrolled_bytes = base64.b64decode(u.face_image)
                enrolled_img = Image.open(io.BytesIO(enrolled_bytes)).convert("RGB")
                
                similarity, is_same = analyzer.compare(enrolled_img, live_img, threshold=0.35)
                print(f"1:N local match comparison with '{u.username}': similarity={similarity:.4f} (match: {is_same})", flush=True)
                
                all_similarities[u.username] = f"{similarity:.4f}"
                if similarity > best_similarity:
                    best_similarity = similarity
                    if is_same:
                        best_user = u
            except Exception as e:
                print(f"Local match error for user {u.username}: {e}", flush=True)
                
        if best_user:
            chat_histories[best_user.username] = []
            from utils import create_access_token
            token = create_access_token(best_user.username)
            return {
                "success": True,
                "token": token,
                "username": best_user.username,
                "name": best_user.name,
                "message": "Face verified successfully!"
            }
        else:
            raise HTTPException(status_code=401, detail="Identity could not be matched. No matching face scan found.")




@router.post("/api/settings/reset-face")
async def reset_face_endpoint(
    request: ResetFaceRequest, 
    session: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    username = request.username.lower().strip()
    if username != current_user:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify other users' settings.")
        
    user = session.exec(select(UserTable).where(UserTable.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    from utils import verify_credential
    db_ans = user.security_answer
    db_mpin = user.mpin
        
    def save_ans_hash(hashed):
        user.security_answer = hashed
        session.add(user)
        session.commit()
        
    def save_mpin_hash(hashed):
        user.mpin = hashed
        session.add(user)
        session.commit()
        
    if not db_ans or not verify_credential(request.security_answer, db_ans, on_success_callback=save_ans_hash):
        raise HTTPException(status_code=400, detail="Incorrect security answer.")
        
    if not db_mpin or not verify_credential(request.mpin, db_mpin, on_success_callback=save_mpin_hash):
        raise HTTPException(status_code=400, detail="Incorrect MPIN.")
        
    user.face_image = request.face_image_base64
    session.add(user)
    session.commit()
    
    return {"success": True, "message": "Face scan enrolled successfully."}


