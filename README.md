# NidhiVani AI (BankVoiceAI)

NidhiVani AI is a cutting-edge, voice-first AI-driven digital banking assistant. It combines a WhatsApp-style interactive conversational interface with advanced biometric authentication, multi-agent orchestration, and secure transactional flows.

---

## Key Features

* **Multi-Agent Orchestration**: Powered by LangGraph, routing user queries to specialized sub-agents (Accounts, Payments, Fixed Deposits, Support).
* **Voice Biometrics**: Speech-based user verification using voice passphrases and audio processing.
* **Facial Authentication**: Secure 1:1 face login to prevent spoofing and unauthorized access.
* **Secure MPIN entry**: Input masking and chat history transcript sanitization for 4-digit MPIN validation.
* **PDF Statement Generator**: Generates and downloads statement logs directly from the UI.
* **Multilingual Localization**: Real-time voice translation and support for multiple Indian languages.

---

## System Architecture

* **Frontend**: Responsive Single-Page Application (SPA) styled with vanilla CSS (glassmorphism design system) and powered by interactive Vanilla Javascript.
* **Backend**: FastAPI (Python) serving REST APIs and managing WebSocket voice streams.
* **Orchestration**: LangGraph state machine managing routing heuristics and dynamic state memory.
* **Database**: PostgreSQL storing account balances, user profiles, face embeddings, and transaction ledgers.
* **Models**: Google Gemini for intent classification and natural language understanding.

For a deeper dive into the system design, check out the [System Architecture Guide](ARCHITECTURE.md).

---

## Security Features

NidhiVani AI uses industry-standard security practices to protect client data:
* **Credential Hashing**: User passwords, 4-digit transaction MPINs, and recovery security answers are securely hashed using the **Argon2id** algorithm (via the `argon2-cffi` library).
* **Auto-Migration Flow**: Any legacy database records with plaintext credentials are automatically upgraded to secure Argon2id hashes upon their first successful verification check, ensuring a seamless and secure migration.
* **Biometric Authentication**: Multi-layered biometric matching (face recognition and voice passphrase checks) controls account access.
* **Input and Transcript Masking**: Frontend input fields and chatbot transcription bubbles dynamically mask sensitive 4-digit MPIN entries to prevent visual exposure.

---

## Project Directory Layout

```
├── static/                 # Frontend assets (HTML, CSS, JS)
│   ├── index.html          # Dashboard UI shell
│   ├── style.css           # Glassmorphism theme and layout
│   └── app.js              # State management, biometric, and chat handlers
├── routers/                # FastAPI endpoint sub-routers
│   ├── accounts.py         # Account details & statements
│   ├── auth.py             # Credentials and biometric auth
│   ├── chat.py             # Chat history and Agent interactions
│   └── payments.py         # Fund transfers and transactions
├── main.py                 # FastAPI app entry point
├── agents_graph.py         # LangGraph state machine & multi-agent routing
├── database.py             # database schemas, models, and mock seeding
├── inference.py            # Face / Voice matching and embedding utilities
├── requirements.txt        # Python dependency manifest
└── .env.template           # Template for environment configuration
```

For specific module walkthroughs, check out the [Function Implementation Guide](FUNCTION_GUIDE.md).

---

## Getting Started

### 1. Prerequisites
Ensure you have **Python 3.11.7** installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.template` to `.env` and fill in your API credentials:
```bash
cp .env.template .env
```
Key variables required:
* `DATABASE_URL`: PostgreSQL connection string.
* `GEMINI_API_KEY`: API key for Gemini models.

### 4. Run Migrations & Seeding
```bash
python migrate_db.py
```

### 5. Launch the Server
```bash
uvicorn main:app --port 8001 --reload
```
Open [http://127.0.0.1:8001](http://127.0.0.1:8001) in your browser.
