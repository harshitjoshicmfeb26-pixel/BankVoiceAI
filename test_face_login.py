import base64
import requests
import os

# Path to the generated test image
IMAGE_PATH = r"C:\Users\vchig\.gemini\antigravity-ide\brain\7cafc0f7-0299-4325-a0bb-fe147148263a\test_face_1786377522114.png"

def test_face_flow():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Test image not found at {IMAGE_PATH}")
        return

    # 1. Read and encode the face image
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()
    base64_image = base64.b64encode(img_bytes).decode("utf-8")

    base_url = "http://127.0.0.1:8001"
    
    import time
    username = f"facetest_{int(time.time())}"
    
    # 2. Register a new user with the face image
    reg_payload = {
        "name": "Face Test User",
        "username": username,
        "password": "password123",
        "mpin": "9999",
        "voice_passphrase": "my face is my key",
        "security_question": "What is your favorite book?",
        "security_answer": "Harry Potter",
        "face_image_base64": base64_image
    }
    
    print(f"Step 1: Attempting to register user '{username}' with face image...")
    try:
        response = requests.post(f"{base_url}/api/register", json=reg_payload)
        print("Registration Status Code:", response.status_code)
        print("Registration Response:", response.json())
    except Exception as e:
        print("Registration Request Failed:", e)
        return
 
    # 3. Attempt to log in with the face image
    login_payload = {
        "username": username,
        "face_image_base64": base64_image
    }
    
    print(f"\nStep 2: Attempting to log in user '{username}' via face recognition...")
    try:
        response = requests.post(f"{base_url}/api/face-login", json=login_payload)
        print("Login Status Code:", response.status_code)
        print("Login Response:", response.json())
    except Exception as e:
        print("Login Request Failed:", e)

if __name__ == "__main__":
    test_face_flow()
