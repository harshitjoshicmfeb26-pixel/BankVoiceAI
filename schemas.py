from typing import Optional
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    voice_passphrase: str
    mpin: str
    initial_savings: float = 1000.0
    initial_checking: float = 500.0
    voice_audio_base64: Optional[str] = None
    voice_audio_mime: Optional[str] = None
    security_question: Optional[str] = None
    security_answer: Optional[str] = None
    face_image_base64: Optional[str] = None

class FaceLoginRequest(BaseModel):
    username: Optional[str] = None
    face_image_base64: str



class VoiceLoginRequest(BaseModel):
    username: Optional[str] = None
    passphrase: str
    voice_audio_base64: Optional[str] = None
    voice_audio_mime: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    username: str
    language: Optional[str] = "en-IN"

class ResetPasswordRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str

class DirectPaymentRequest(BaseModel):
    username: str
    recipient_username: str
    amount: float
    source_account: str
    mpin: str

class ResetVoiceRequest(BaseModel):
    username: str
    security_answer: str
    new_voice_phrase: str
    voice_audio_base64: Optional[str] = None
    voice_audio_mime: Optional[str] = None

class ResetFaceRequest(BaseModel):
    username: str
    security_answer: str
    face_image_base64: str

