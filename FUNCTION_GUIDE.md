# NidhiVani Voice Banking Assistant - Code & Function Guide

This guide is designed to help you explain the inner workings of the codebase to an interviewer or teammate. It breaks down the key functions across authentication, conversation flow, database tools, and logging.

---

## 🔐 1. Authentication & Voice Biometric Verification

### `voice_login_endpoint(request, session)`
* **Location**: `routers/auth.py`
* **Why it is used**: Authenticates users using a combination of a spoken voice passphrase, username (optional), and voice print biometrics.
* **What it does**: 
  - Validates the passphrase matches the user's registered voice passphrase.
  - If a recorded voice print exists for the user, it verifies the speaker's voice using the Gemini API.
  - If no voice print exists (e.g. legacy/dummy accounts), it gracefully falls back to passphrase verification alone so they can still log in.
* **Flow**:
  1. Retrieve the user profile from the database matching the username (or loops through all users to find a matching passphrase if no username is typed).
  2. Call `check_passphrase_similarity` to see if what the user said matches their registered passphrase.
  3. Look in the `voices/` directory for an enrolled print (`voices/{username}_enroll.webm` or `.wav`).
  4. **If found**: Decodes the base64 audio payload from the request, reads the enrolled file, and calls the `gemini-3.6-flash` model with both audio clips.
  5. Ask the model: *"Compare the speaker's voice... Are they the same person? Respond 'Yes' or 'No'"*.
  6. **If Gemini rate limits/fails**: Resiliently logs a warning and falls back to passphrase similarity approval to prevent lockout.
  7. Return success or failure response.

### `check_passphrase_similarity(registered, spoken)`
* **Location**: `utils.py`
* **Why it is used**: Validates that the spoken phrase matches the registered passphrase, accounting for transcription inaccuracies or small verbal changes.
* **What it does**: Cleans both strings and performs three sequential matching tests:
  1. **Direct Match**: Exact string or substring match.
  2. **Jaccard Word Similarity**: Measures the word overlap ratio (succeeds if $\ge 70\%$ unique word match).
  3. **Character Sequence Ratio**: Uses python's `difflib.SequenceMatcher` to measure character-by-character similarity (succeeds if $\ge 70\%$).
* **Flow**: Input $\rightarrow$ Strip punctuation/lowercase $\rightarrow$ Direct match check $\rightarrow$ Jaccard word set calculation $\rightarrow$ SequenceMatcher comparison $\rightarrow$ Boolean result.

---

## 💬 2. Core Conversational Engine & Intent Routing

### `chat_endpoint(request, session)`
* **Location**: `routers/chat.py`
* **Why it is used**: The primary backend gateway for the AI voice assistant. It handles user messages, session contexts, security checks, and routes processing to the LLM agent graph.
* **What it does**:
  - Intercepts messages if the user is in a "pending transfer" state to verify their 4-digit MPIN before finalizing transaction writes.
  - Resolves recipients locally if the user is in the middle of a transfer request.
  - Feeds the conversational history into the LangGraph multi-agent network.
  - Automatically falls back to a local multilingual simulation routing if the Gemini API is offline or has reached its rate limits.
* **Flow**:
  1. Set the thread-local context variable `current_user_var` to the logged-in user.
  2. **Pending Check**: If `username` is in `pending_transfers`:
     - If user says *"cancel"*, abort the transaction.
     - If user says/enters a 4-digit number, verify it matches their database MPIN. If correct, execute the transfer and insert Transaction records. If incorrect, increment attempts (locks/logs out on 3rd failure).
  3. **Standard Run**: If no pending transfer, call the LangGraph `agents_graph.invoke(inputs)`.
  4. Parse the generated content response and return the text along with the updated database state.
  5. **Exception Handler**: If LangGraph throws a quota exception, activate simulation fallback (regular expression keyword parsing) to simulate account/FD operations.

### `classify_intent_heuristically(messages)`
* **Location**: `agents_graph.py`
* **Why it is used**: Latency Optimization. It bypasses slow, expensive LLM-based intent routing by classifying the query locally.
* **What it does**: Uses regex and keyword matching to map common user questions directly to `account`, `fd`, or `support` specialists.
* **Flow**:
  - Checks if the user is saying a short greeting ("hello", "namaste") $\rightarrow$ routes directly to `support`.
  - Checks for phrases containing account keywords ("balance", "checking", "send money", "transactions") $\rightarrow$ routes directly to `account`.
  - Checks for FD phrases ("fixed deposit maturity", "my fd") $\rightarrow$ routes directly to `fd`.
  - If no clear matching keyword sets are found, returns `None` to fallback to the `router_llm` classifier.

### `router_node(state)`
* **Location**: `agents_graph.py`
* **Why it is used**: Classifies intent when local heuristic routing is uncertain.
* **What it does**: Uses `router_llm` (`gemini-3.6-flash`) as a receptionist. It looks at the prompt history and returns a single word: `'account'`, `'fd'`, or `'support'`.
* **Flow**: Input state $\rightarrow$ Run Heuristics $\rightarrow$ If None, construct system prompt $\rightarrow$ Call LLM classifier $\rightarrow$ Update `next_agent` edge state.

---

## 🛠️ 3. Agent specialist Nodes & Tool Execution

### `account_agent_node(state)` / `fd_agent_node(state)`
* **Location**: `agents_graph.py`
* **Why it is used**: Implements the specialized system prompt boundaries for specific banking divisions.
* **What it does**: Inject instructions detailing user context, force responses strictly in the requested language (English, Hindi, or Marathi), and invoke the LLM with access to specific Python tools.
* **Flow**: Format system prompt with user data $\rightarrow$ Invoke LLM $\rightarrow$ Check if LLM requested a tool call $\rightarrow$ Transition to tool execution or finalize output text.

### `tool_execution_node(state)`
* **Location**: `agents_graph.py`
* **Why it is used**: LangGraph node that executes database operations on behalf of the agent.
* **What it does**: Iterates through the list of `tool_calls` requested by the agent LLM, maps them to helper functions, runs them, packages results in a `ToolMessage`, and loops back to the agent to summarize.

---

## 🏦 4. Database Tools & Utilities

### `send_money(recipient, amount, source_account)`
* **Location**: `assistant.py` (Exposed as an LLM Tool)
* **Why it is used**: Prepares a secure money transfer from the user's account to a recipient.
* **What it does**:
  - Validates balances and checks if the recipient exists.
  - If the recipient's name is spoken in Devanagari (Hindi/Marathi), it calls the Gemini API to dynamically resolve it phonetically to a database username.
  - Stashes the transaction details in the `pending_transfers` dictionary.
  - Returns a `PENDING_CONFIRMATION` instruction prompting the user to state their MPIN. (This separates initiation from execution, ensuring voice control safety!).

### `get_user_current_state(username, session)`
* **Location**: `utils.py`
* **Why it is used**: Collects the full banking profile state to refresh the UI dashboard.
* **What it does**: Queries the database to retrieve:
  - Savings and checking balances.
  - The 10 most recent transactions.
  - List of active fixed deposits.
  Returns this aggregated package in a JSON-ready dictionary.

---

## 📊 5. Monitoring & Metric Logging

### `log_token_usage(agent_name, usage_metadata)`
* **Location**: `utils.py`
* **Why it is used**: Tracks execution overhead, costs, and token statistics for all generative model calls.
* **What it does**:
  - Captures input tokens, output tokens, and total tokens from model responses.
  - Formats and writes the stats as a JSON line into `token_usage.log`.
  - Prints a console log indicating the agent name and usage parameters.
* **Flow**: Receive metadata dict $\rightarrow$ Get token counts $\rightarrow$ Append JSON line $\rightarrow$ Output terminal print message.
