# Session Handoff & Continuity State — NidhiVani AI

**Date:** October 3, 2026 (Afternoon Session Checkpoint)  
**Status:** All code staged, compound branch/product query disambiguation resolved, tests passing 100% (26/26), live server active on port 8001.

---

## 1. Accomplishments & Latest Updates

### Compound Branch + Product Query Disambiguation (Solved):
* **Root Cause Identified**:
  When a user submitted a query containing both a branch name and a product policy (e.g., *"pune waali branch main fd ka interest rate kya milega?"*), the RAG matching in `rag_service.py` gave a city phrase boost (+6) to the Pune Branch chunk without sufficient weight given to product anchors or rate policies. As a result, the Support Specialist received the branch address chunk and answered with the branch address instead of the Fixed Deposit interest rates.
* **Fixes Implemented**:
  1. **Colloquial Stop Words**: Added `"main"`, `"wali"`, `"waali"`, `"wala"`, `"wale"` to `stop_words` in [rag_service.py](file:///c:/Users/HARSH/AI_Work/BankVoiceAI/rag_service.py).
  2. **Product Anchors**: Added dedicated detection for FD, Savings, Loan, and RD (`is_fd_query`, `is_savings_query`, etc.) granting a +8 anchor boost.
  3. **Policy Priority Hierarchy**: When a policy/rate intent is detected without location/address intent (`has_policy_intent and not has_location_intent`), chunks in rates/limits/compliance receive a +4 priority boost.
  4. **Multi-Word Key Phrases**: Added `"interest rate"`, `"interest rates"`, `"ब्याज दर"`, `"व्याज दर"` to phrase boosts (+6).
  5. **Model Quota Management**: Transitioned LLMs in [agents_graph.py](file:///c:/Users/HARSH/AI_Work/BankVoiceAI/agents_graph.py) and [assistant.py](file:///c:/Users/HARSH/AI_Work/BankVoiceAI/assistant.py) to `gemini-3.5-flash` to prevent `429 RESOURCE_EXHAUSTED` errors on exhausted model quotas.

### Verification & Live Testing:
* **Live HTTP Verification** ([http://127.0.0.1:8001/api/chat](http://127.0.0.1:8001/api/chat)):
  - Query: *"pune waali branch main fd ka interest rate kya milega?"*  
    $\rightarrow$ Response: *"पुणे शाखा में फिक्स्ड डिपॉजिट (FD) पर ब्याज दरें 1 साल के लिए 6.80% और 3 साल के लिए अधिकतम 7.10% हैं। वरिष्ठ नागरिकों को सभी अवधियों पर 0.50% का अतिरिक्त ब्याज मिलता है।"* (100% Devanagari Hindi, exact rates provided).
  - Query: *"pune branch cha ifsc code kay ahe"*  
    $\rightarrow$ Response: *"पुणे शाखेचा आयएफएससी (IFSC) कोड NIDH0002001 हा आहे. ही शाखा फर्ग्युसन कॉलेज रोड, डेक्कन जिमखाना येथे स्थित आहे।"* (100% Devanagari Marathi, exact IFSC and location).
* **Comprehensive Test Suite**:
  - [test_rag_comprehensive.py](file:///c:/Users/HARSH/AI_Work/BankVoiceAI/test_rag_comprehensive.py): **26/26 tests passing (100.0%)** with an average latency of **2.12 ms** per query.

---

## 2. Server & Infrastructure State

* **Uvicorn Daemon**: Active on [http://127.0.0.1:8001](http://127.0.0.1:8001).
* **Database**: PostgreSQL on `localhost:5432/banking` (`pgvector` active).
* **Git Status**: All files ready for commit (`git add -A`).
* **Credentials**: `.env` safely excluded by `.gitignore`.

---

## 3. Next Steps

1. **User Acceptance Testing**:
   - Open [http://127.0.0.1:8001](http://127.0.0.1:8001) in browser and test queries in the web UI.
2. **Commit & Push**:
   ```bash
   git add -A
   git commit -m "fix: compound branch/rate query disambiguation and switch to gemini-3.5-flash"
   git push origin main
   ```
3. **Resume Mastering Roadmap**:
   - Module 13: Prompt Engineering & Guardrail Policies.
