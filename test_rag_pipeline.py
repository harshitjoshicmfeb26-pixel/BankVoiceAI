import sys
from sqlmodel import Session, select
from database import engine, init_db
from models import BankKnowledgeChunk
from rag_service import search_knowledge_base
from agents_graph import agents_graph

# Configure UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("--- 1. DATABASE & TABLE VERIFICATION ---")
init_db()
from rag_service import init_knowledge_base
init_knowledge_base(force=True)

with Session(engine) as session:
    chunks = session.exec(select(BankKnowledgeChunk)).all()
    print(f"Total Knowledge Chunks in PostgreSQL: {len(chunks)}")
    assert len(chunks) >= 15, f"Expected at least 15 chunks, got {len(chunks)}"

print("\n--- 2. MULTILINGUAL SEARCH VERIFICATION ---")

test_cases = [
    {
        "desc": "English FD Rates Query",
        "query": "What is your senior citizen fixed deposit rate?",
        "lang": "en-in",
        "expected_sub": "7.30%"
    },
    {
        "desc": "Hindi Loan Query",
        "query": "होम लोन की ब्याज दर क्या है?",
        "lang": "hi-in",
        "expected_sub": "8.40%"
    },
    {
        "desc": "Marathi Branch Hours Query",
        "query": "बँकेची कामकाजाची वेळ काय आहे?",
        "lang": "mr-in",
        "expected_sub": "10:00"
    },
    {
        "desc": "English Cyber Fraud Helpline Query",
        "query": "What number should I call for cyber fraud or stolen money?",
        "lang": "en-in",
        "expected_sub": "1930"
    },
    {
        "desc": "Hindi Voice Transfer Cap Query",
        "query": "आवाज से पैसे भेजने की सीमा क्या है?",
        "lang": "hi-in",
        "expected_sub": "10,000"
    },
    {
        "desc": "Marathi KYC Documents Query",
        "query": "केवायसी साठी कोणती कागदपत्रे लागतात?",
        "lang": "mr-in",
        "expected_sub": "आधार"
    },
    {
        "desc": "Off-topic Query Fallback",
        "query": "How is the weather in Paris today?",
        "lang": "en-in",
        "expected_sub": "could not find an official bank policy"
    }
]

passed = 0
for tc in test_cases:
    res = search_knowledge_base(tc["query"], tc["lang"])
    ans = res["answer"]
    has_expected = tc["expected_sub"] in ans
    status = "PASS" if has_expected else "FAIL"
    if has_expected:
        passed += 1
    print(f"[{status}] {tc['desc']}")
    print(f"       Query : {tc['query']}")
    print(f"       Answer: {ans[:90]}...\n")

print(f"Search Tests Passed: {passed}/{len(test_cases)}")
assert passed == len(test_cases), "Some search tests failed!"

print("--- 3. LANGGRAPH AGENT GRAPH COMPILATION ---")
assert agents_graph is not None
print("LangGraph StateGraph compiled with support RAG tool successfully!")

print("=" * 60)
print("ALL OFFLINE POSTGRESQL RAG TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
