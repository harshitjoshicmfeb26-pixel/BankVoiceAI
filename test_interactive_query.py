import sys
from rag_service import search_knowledge_base, detect_query_language

# Ensure Devanagari UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("=" * 70)
    print("NIDHIVANI AI: INTERACTIVE MULTILINGUAL RAG TESTER")
    print("=" * 70)
    print("Type any query in English, Hinglish, Marathlish, Hindi, or Marathi.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            query = input("Your Query > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                print("Exiting. Goodbye!")
                break

            detected_lang = detect_query_language(query, "en-in")
            result = search_knowledge_base(query, language=detected_lang)

            print("\n" + "-" * 50)
            print(f"[Language] Detected : {detected_lang}")
            print(f"[Topic]    Matched  : {result.get('title')}")
            print(f"[Score]    Relevance: {result.get('score')}")
            print(f"[Answer]   Response :\n{result.get('answer')}")
            print("-" * 50 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break

if __name__ == "__main__":
    main()
