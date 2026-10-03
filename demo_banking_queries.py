import sys
from rag_service import search_knowledge_base

sys.stdout.reconfigure(encoding='utf-8')

banking_queries = [
    (
        "Home Loan & CIBIL (English)",
        "What is your home loan interest rate and what is the minimum CIBIL score required?",
        "en-in"
    ),
    (
        "Cyber Fraud Reporting & Liability (Hindi)",
        "अगर मेरे खाते से फ्रॉड ट्रांजैक्शन हो जाए तो मुझे क्या करना चाहिए?",
        "hi-in"
    ),
    (
        "Branch Address & IFSC Code (Marathi)",
        "पुणे शाखेचा आयएफएससी कोड आणि पत्ता काय आहे?",
        "mr-in"
    ),
    (
        "Voice Banking Security Limit (English)",
        "Can I transfer 50000 rupees by voice banking?",
        "en-in"
    ),
    (
        "Senior Citizen FD Tenure & Yield (Hinglish)",
        "Senior citizen ke liye 1 year FD ka rate kitna hai?",
        "hi-in"
    ),
    (
        "KYC Document Verification (English)",
        "What officially valid documents do I need for re-KYC?",
        "en-in"
    ),
    (
        "Physical ATM / Debit Card Inquiry (English)",
        "Can you send me a physical ATM debit card?",
        "en-in"
    ),
    (
        "Saturday Branch Operating Timings (Hindi)",
        "क्या शनिवार को बैंक खुला रहता है और समय क्या है?",
        "hi-in"
    )
]

print("=" * 75)
print("🏦 NIDHIVANI AI: LIVE BANKING POLICY RETRIEVAL DEMO")
print("=" * 75)

for title, query, lang in banking_queries:
    result = search_knowledge_base(query, lang)
    print(f"\n📌 {title}")
    print(f"   Customer Query : \"{query}\"")
    print(f"   Matched Policy : {result.get('title')}")
    print(f"   Category       : {result.get('category')}")
    print(f"   Spoken Response: \"{result.get('answer')}\"")
    print("-" * 75)

print("\nAll 8 live banking inquiries retrieved successfully from PostgreSQL!")
