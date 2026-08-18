import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

user_list_str = """
- Username: browseruser, Name: Test Browser User
- Username: charlie, Name: Charlie Brown
- Username: david, Name: David Miller
- Username: emma, Name: Emma Watson
- Username: pranali, Name: pranali
- Username: sujith, Name: sujith
- Username: test1, Name: test1
- Username: tester, Name: Tester
- Username: testrecipient, Name: Test Recipient
- Username: testuser, Name: Test User
- Username: testvoice, Name: Test Voice
- Username: thomas, Name: thomas
- Username: umaya, Name: umaya
- Username: user1, Name: user1
- Username: varsha, Name: varsh
- Username: varsha1, Name: varsha1
- Username: bob, Name: Bob Jones
- Username: admin, Name: Admin
- Username: alice, Name: Alice Smith
- Username: aman, Name: aman
"""

prompt = (
    f"You are a database entity resolution assistant. The user wants to transfer money to a person.\n"
    f"Spoken/written recipient name: 'बॉब'\n"
    f"List of available users in the database:\n"
    f"{user_list_str}\n\n"
    f"Find the database user whose username or name matches the spoken recipient name (which may be in a different language/script like Hindi, Marathi, Devanagari, or phonetic English).\n"
    f"Respond with ONLY the exact username of the matching user. If there is no match, respond with 'None'. Do not write any other text."
)

response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=prompt
)
print("Response text:", repr(response.text))
