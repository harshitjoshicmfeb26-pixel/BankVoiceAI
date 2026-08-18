import base64
import requests
import os

def test_successful_voice_login():
    url = "http://127.0.0.1:8001/api/voice-login"
    
    # Read alice's enrolled audio file to use as the login voice audio (perfect match)
    audio_path = "voices/alice_enroll.webm"
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found. Cannot perform test.")
        return
        
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
        
    base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    
    payload = {
        "username": "alice",
        "passphrase": "my voice is my secure password",
        "voice_audio_base64": base64_audio,
        "voice_audio_mime": "audio/webm"
    }
    
    print("Sending voice login request for alice...")
    try:
        response = requests.post(url, json=payload)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except Exception as e:
        print("API Call failed:", e)

def test_failed_voice_login_incorrect_passphrase():
    url = "http://127.0.0.1:8001/api/voice-login"
    
    payload = {
        "username": "alice",
        "passphrase": "wrong passphrase here",
    }
    
    print("\nSending voice login request for alice with incorrect passphrase...")
    try:
        response = requests.post(url, json=payload)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except Exception as e:
        print("API Call failed:", e)

def test_voice_login_any_speaker_succeeds():
    url = "http://127.0.0.1:8001/api/voice-login"
    
    # Read bob's voice (completely different speaker from alice)
    audio_path = "bob.wav"
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found. Cannot perform test.")
        return
        
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
        
    base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    
    payload = {
        "username": "alice",
        "passphrase": "my voice is my secure password",
        "voice_audio_base64": base64_audio,
        "voice_audio_mime": "audio/wav"
    }
    
    print("\nSending voice login request for alice using bob's voice audio print...")
    try:
        response = requests.post(url, json=payload)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except Exception as e:
        print("API Call failed:", e)

if __name__ == "__main__":
    test_successful_voice_login()
    test_failed_voice_login_incorrect_passphrase()
    test_voice_login_any_speaker_succeeds()
