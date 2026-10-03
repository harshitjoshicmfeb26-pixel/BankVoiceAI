# NidhiVani AI (BankVoiceAI)

NidhiVani AI is a cutting-edge, voice-first digital banking assistant built for Indian banking ecosystems. It combines a sleek glassmorphic conversational interface with advanced biometric authentication, multi-agent LangGraph orchestration, 100% offline PostgreSQL RAG (Retrieval-Augmented Generation), and resilient multi-model failover.

---

## 🌟 Key Features

* **Multi-Agent Orchestration**: Built on **LangGraph**, intelligent routing coordinates specialized sub-agents:
  * **Receptionist / Router**: High-speed heuristic & semantic intent classification.
  * **Account Specialist**: Balances, ledgers, transaction history, and fund transfers.
  * **Fixed Deposit Specialist**: Personal FD portfolio, rates, and maturity details.
  * **Support Specialist**: Banking policies, branch locations, interest rates, and compliance.
* **100% Offline Multilingual PostgreSQL RAG**:
  * 18 curated, authoritative policy chunks derived from bank regulatory documentation stored directly in PostgreSQL (`bank_knowledge_chunk`).
  * Sub-3ms deterministic retrieval latency across English, Hindi, and Marathi.
  * Zero external embedding model downloads or third-party vector search dependencies.
* **Cross-Script & Colloquial Understanding**:
  * Seamlessly understands Hindi and Marathi written in English (Hinglish/Marathlish, e.g., *"pune waali branch main fd ka interest rate kya milega?"*).
  * Dynamic phonetic vocabulary mapping (`ROMAN_PHONETIC_BANKING_MAP`) expands Romanized terms into Devanagari tokens.
  * Automatically forces 100% native Devanagari script output and Indian neural Text-to-Speech (TTS) voice routing.
* **Compound Query Disambiguation**:
  * Sophisticated product anchor boosting (`is_fd_query`, `is_savings_query`, `is_loan_query`, `is_rd_query`) separates inquiries about bank-wide interest rate policies from physical branch locators.
* **Automated Multi-Tier Model Failover**:
  * Primary: **`gemini-3.5-flash`** with automatic failover via LangChain's `.with_fallbacks()` to **`gemini-3.5-flash-lite`**.
  * Guaranteed resilience against API quota limits (`429 RESOURCE_EXHAUSTED`), cloud outages (`503`), or model deprecations, gracefully falling back to a local deterministic simulator if all external APIs are unreachable.
* **Bank-Grade Security**:
  * **Argon2id Hashing**: Passwords, 4-digit MPINs, and security answers hashed via `argon2-cffi`.
  * **Input & Transcript Masking**: Interactive MPIN entries and conversational transaction bubbles are dynamically sanitized.
  * **Account Boundaries**: Support Specialist is strictly sandboxed from accessing private account balances.
* **Biometric Authentication**: Multi-layered face recognition (1:1 embedding matching) and voice passphrase verification.
* **PDF Statement Generator**: Instant generation and download of account statements directly from the web interface.

---

## 🏗️ System Architecture

* **Frontend**: Vanilla CSS glassmorphism SPA with native Web Speech API (STT & TTS) and responsive audio waveforms.
* **Backend**: FastAPI (Python 3.11) managing REST endpoints, JWT session authentication, and WebSocket streams.
* **Orchestration**: LangGraph state machine with dynamic `ContextVar` session tracking (`current_language_var`, `current_user_var`).
* **Database**: PostgreSQL with `pgvector` extension enabled, managed via SQLModel / SQLAlchemy.
* **Language Models**: Google Gemini 3.5 series with automated tool-calling (`search_bank_knowledge_base`, `get_transaction_history`, `send_money`, `get_balance`).

---

## 📂 Project Directory Layout

```
├── data/
│   └── knowledge_base/             # Authoritative banking policy documents
│       ├── banking_operations_and_limits.md
│       ├── branches_and_contacts.md
│       ├── interest_rates_and_charges.md
│       └── kyc_and_fraud_protection.md
├── routers/                        # FastAPI sub-routers
│   ├── accounts.py                 # Account summaries & PDF statements
│   ├── auth.py                     # Argon2id authentication & biometric login
│   ├── chat.py                     # Chat endpoints & LangGraph dispatch
│   └── payments.py                 # Fund transfers & ledger logging
├── static/                         # Frontend SPA assets
│   ├── index.html                  # Dashboard & voice interaction UI
│   ├── style.css                   # Glassmorphic CSS design system
│   └── app.js                      # Voice recording, TTS, and state handlers
├── agents_graph.py                 # LangGraph multi-agent workflow & model failovers
├── assistant.py                    # Database tools & recipient resolution
├── database.py                     # PostgreSQL connection & SQLModel metadata
├── models.py                       # UserTable, TransactionTable, BankKnowledgeChunk
├── rag_service.py                  # PostgreSQL RAG engine & cross-script search
├── main.py                         # FastAPI application entrypoint
├── test_rag_comprehensive.py       # 26-case automated RAG test suite
├── SESSION_HANDOFF.md              # Current session state & continuity notes
├── requirements.txt                # Python dependencies manifest
└── .env.template                   # Environment variable template
```

---

## 📚 Knowledge Base Coverage

| Category | Topics Covered | Key Facts & Thresholds |
| :--- | :--- | :--- |
| **Rates** | Savings, Fixed Deposits, Recurring Deposits, Loans | FD: 1-Yr 6.80%, 3-Yr 7.10% (Senior Citizen +0.50% $\rightarrow$ 7.30%). Savings: 3.00% to 4.00%. Home Loan: 8.40%. |
| **Limits** | IMPS, NEFT, RTGS, Voice Banking Caps | IMPS: ₹2L per tx, ₹5L daily. Voice Transfer Security Cap: ₹10,000 per tx, ₹25,000 daily (Mandatory MPIN). |
| **Compliance** | KYC, Re-KYC, Cyber Fraud, Lost Cards | Accepted: Passport, Driving Licence, Aadhaar, Voter ID. Cyber Fraud: 1930 Helpline, 72-hr Zero Liability. |
| **Branches** | Mumbai, Pune, Delhi Central, Timings | Pune: FC Road (IFSC: NIDH0002001). Mumbai: Nariman Point (IFSC: NIDH0001001). Delhi: Connaught Place (IFSC: NIDH0003001). |

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python 3.11+**
* **PostgreSQL** running locally with database `banking` created:
  ```sql
  CREATE DATABASE banking;
  ```

### 2. Install Dependencies
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.template` to `.env`:
```bash
cp .env.template .env
```
Ensure the following variables are configured:
* `DATABASE_URL`: `postgresql://postgres:<password>@localhost:5432/banking`
* `GEMINI_API_KEY`: Your Google AI Studio API key.
* `SECRET_KEY`: Random secret string for JWT token generation.

### 4. Database Initialization & Seeding
Start the server or run the test suite to automatically initialize tables and seed the 18 multilingual knowledge base chunks:
```bash
python test_rag_comprehensive.py
```

### 5. Launch the Server
```bash
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```
Open [http://127.0.0.1:8001](http://127.0.0.1:8001) in your browser.

---

## 🧪 Testing & Validation

Run the comprehensive 26-test RAG suite covering all 6 banking categories, cross-script queries, compound branch/rate queries, and security guardrails:

```bash
python test_rag_comprehensive.py
```

Expected Output:
```
======================================================================
📊 SUMMARY: 26/26 Tests Passed (100.0%)
⚡ AVERAGE RETRIEVAL LATENCY: 2.12 ms per query
======================================================================
```
