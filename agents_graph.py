import os
import re
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Import database/agent tools
from assistant import get_transaction_history, send_money, get_fixed_deposit_details, get_balance
from utils import log_token_usage

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize models
# We instantiate them if the API key is configured. If not, they will raise an exception on invoke,
# which routes.py will catch and fall back to Simulation Mode.
router_llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key, temperature=0.0, max_retries=1)
account_llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key, temperature=0.2, max_retries=1)
fd_llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key, temperature=0.2, max_retries=1)
support_llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key, temperature=0.2, max_retries=1)

# Bind tools to the LLMs that use them
account_llm_with_tools = account_llm.bind_tools([get_transaction_history, send_money, get_balance])
fd_llm_with_tools = fd_llm.bind_tools([get_fixed_deposit_details])

# Define the state of our agent graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    active_agent_name: str
    db_user_name: str
    language_name: str

# --- Intent Classification Heuristics ---

def classify_intent_heuristically(messages: list) -> str:
    if not messages:
        return None
        
    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return None
        
    msg = last_msg.content.lower().strip()
    
    # Strip basic punctuation while keeping alphanumeric and Devanagari Unicode ranges
    msg_clean = re.sub(r"[^\w\s\u0900-\u097F]", "", msg)
    words = msg_clean.split()
    
    if not words:
        return None

    # 1. Greetings and identity checking (direct to support)
    greetings = {
        "hi", "hello", "hey", "hola", "namaste", "morning", "afternoon", "evening", 
        "नमस्कार", "नमस्ते", "हॅलो", "हाय"
    }
    identity_phrases = [
        "who are you", "what is your name", "help me", "how to use", 
        "तुम कौन हो", "तुम्हारा नाम क्या है", "मदत"
    ]
    if any(w in greetings for w in words) and len(words) <= 3:
        return "support"
    if any(phrase in msg_clean for phrase in identity_phrases):
        return "support"

    # 2. Key phrases mappings
    account_phrases = [
        "how much money", "check balance", "account balance", "my balance", 
        "transaction history", "last transactions", "bank statement", "send money", 
        "transfer money", "send to", "pay to", "transfer to", "checking account", 
        "savings account", "पैसे पाठवा", "पैसे पाठवणे", "पैसे पाठवायचे", 
        "पैसे पाठवायचे आहेत", "पैसे पाठव", "पैसे पाठवायचेत", "पैसे ट्रान्सफर", 
        "पैसे पाठवायला", "पैसे पाठवायचे आहे"
    ]
    if any(phrase in msg_clean for phrase in account_phrases):
        return "account"

    fd_phrases = [
        "fixed deposit details", "my fd", "fd account", "fd maturity", 
        "fixed deposit status", "सावधि जमा"
    ]
    if any(phrase in msg_clean for phrase in fd_phrases):
        return "fd"

    support_phrases = [
        "branch location", "where is the branch", "timings", "opening hours", 
        "closing hours", "customer care", "customer support", "loan rates", 
        "loan details", "interest rates", "credit card", "debit card"
    ]
    if any(phrase in msg_clean for phrase in support_phrases):
        return "support"

    # 3. Keyword check
    account_keywords = {
        "send", "transfer", "balance", "checking", "savings", "statement", 
        "transaction", "history", "money", "pay", "debit", "credit", 
        "rupee", "rupees", "rs", "transferring", "account", "accounts",
        "भेज", "हस्तांतरण", "पैसे", "बैलेंस", "शेष", "शिल्लक", "व्यवहार", "इतिहास", "लेन"
    }
    
    fd_keywords = {
        "fd", "fds", "fixed", "deposit", "deposits", "maturity", "tenure", "booking", "interest",
        "सावधि", "मुदत"
    }
    
    support_keywords = {
        "hours", "timing", "timings", "location", "locations", "branch", "branches", 
        "customer", "care", "support", "help", "loan", "loans", "card", "cards", "policy", "policies"
    }
    
    # Check word overlaps
    has_account = any(w in account_keywords for w in words)
    has_fd = any(w in fd_keywords for w in words)
    has_support = any(w in support_keywords for w in words)
    
    # If there is a single clear category match, return it
    if has_account and not has_fd and not has_support:
        return "account"
    if has_fd and not has_account and not has_support:
        return "fd"
    if has_support and not has_account and not has_fd:
        return "support"
        
    # 4. Check for numeric messages (amount or MPIN) or simple confirmations
    is_number = msg_clean.isdigit() or re.match(r"^\d+(\.\d+)?\s*(rs|rupees|rupee)?$", msg_clean)
    is_confirmation = any(w in msg for w in ["yes", "no", "cancel", "abort", "ok", "sure", "confirm", "stop", "रद्द"])
    
    if is_number or is_confirmation:
        # Check history to find the last AI response context
        for m in reversed(messages[:-1]):
            if isinstance(m, AIMessage):
                content = m.content.lower()
                if any(w in content for w in ["transfer", "mpin", "recipient", "amount", "savings", "checking", "balance"]):
                    return "account"
                if any(w in content for w in ["fixed deposit", "fd", "maturity", "tenure"]):
                    return "fd"
                break
                
    return None

# --- Graph Node Functions ---

def router_node(state: AgentState):
    messages = state["messages"]
    
    # Try heuristic classification to bypass slow LLM routing call
    heuristic_route = classify_intent_heuristically(list(messages))
    if heuristic_route:
        print(f"Heuristically routed to: {heuristic_route}", flush=True)
        return {"next_agent": heuristic_route}
        
    router_instruction = (
        "You are the NidhiVani AI Receptionist / Router. Your job is to classify the user's latest message intent, "
        "in context of the conversation history, into one of three categories: 'account', 'fd', or 'support'.\n"
        "- Choose 'account' if the query is related to checking balances, account limits, details, status, transaction history/ledgers, sending money, or anything related to the user's personal bank accounts.\n"
        "- Choose 'fd' if they ask about fixed deposits or FDs.\n"
        "- Choose 'support' if they ask general questions (e.g., branch timings, branch locations, interest rates, customer care, support policies, general loan details, etc.) that are NOT specific to their personal bank accounts.\n"
        "You must respond with EXACTLY one word: either 'account', 'fd', or 'support'. Do not write anything else."
    )
    
    router_messages = [SystemMessage(content=router_instruction)] + list(messages)
    
    classification_response = router_llm.invoke(router_messages)
    if hasattr(classification_response, "usage_metadata"):
        log_token_usage("Router Node (LLM)", classification_response.usage_metadata)
    raw_content = classification_response.content
    if isinstance(raw_content, list):
        classification = "".join([part if isinstance(part, str) else part.get("text", "") if isinstance(part, dict) else str(part) for part in raw_content]).strip().lower()
    else:
        classification = str(raw_content).strip().lower()
    
    if "fd" in classification:
        next_agent = "fd"
    elif "support" in classification:
        next_agent = "support"
    else:
        next_agent = "account"
        
    return {"next_agent": next_agent}

def account_agent_node(state: AgentState):
    messages = state["messages"]
    db_user_name = state.get("db_user_name", "")
    lang_name = state.get("language_name", "English")
    
    system_instruction = (
        f"You are the Accounts and Transactions Specialist for 'NidhiVani AI'. "
        f"You are assisting logged in user '{db_user_name}'. "
        f"You MUST respond to the user strictly in the {lang_name} language (using the correct script, e.g., Devanagari for Hindi and Marathi). "
        f"Use the tools provided to access their accounts or send money. "
        f"If they ask to send money, use the send_money tool. Always verify if they specify checking/savings source; default to savings if unspecified. "
        f"If they ask for transaction history, use the get_transaction_history tool. "
        f"Keep your responses friendly, polite, and very short, optimized for voice text-to-speech."
    )
    
    # Compile messages including system instruction
    formatted_messages = [SystemMessage(content=system_instruction)] + list(messages)
    response = account_llm_with_tools.invoke(formatted_messages)
    if hasattr(response, "usage_metadata"):
        log_token_usage("Account Specialist Agent", response.usage_metadata)
    
    return {
        "messages": [response],
        "active_agent_name": "Account Specialist"
    }

def fd_agent_node(state: AgentState):
    messages = state["messages"]
    db_user_name = state.get("db_user_name", "")
    lang_name = state.get("language_name", "English")
    
    system_instruction = (
        f"You are the Fixed Deposit and Investment Advisor for 'NidhiVani AI'. "
        f"You are assisting logged in user '{db_user_name}'. "
        f"You MUST respond to the user strictly in the {lang_name} language (using the correct script, e.g., Devanagari for Hindi and Marathi). "
        f"Use the get_fixed_deposit_details tool to answer queries about their fixed deposits. "
        f"Keep your responses friendly, polite, and very short, optimized for voice text-to-speech."
    )
    
    formatted_messages = [SystemMessage(content=system_instruction)] + list(messages)
    response = fd_llm_with_tools.invoke(formatted_messages)
    if hasattr(response, "usage_metadata"):
        log_token_usage("Fixed Deposit Specialist Agent", response.usage_metadata)
    
    return {
        "messages": [response],
        "active_agent_name": "Fixed Deposit Specialist"
    }

def support_agent_node(state: AgentState):
    messages = state["messages"]
    db_user_name = state.get("db_user_name", "")
    lang_name = state.get("language_name", "English")
    
    system_instruction = (
        f"You are the General Customer Support Agent for 'NidhiVani AI'. "
        f"You are assisting logged in user '{db_user_name}'. "
        f"You MUST respond to the user strictly in the {lang_name} language (using the correct script, e.g., Devanagari for Hindi and Marathi). "
        f"Answer general inquiries (e.g. branch hours, locations, general bank policies, loan rates). "
        f"Note that NidhiVani AI does NOT offer any debit cards, credit cards, or card-related services. If the user asks about cards or blocking cards, politely inform them that NidhiVani AI does not support card services. "
        f"You do not have access to any account tools, so you cannot transfer money or look up account details. "
        f"If the user asks for account details or transactions, kindly let them know they should ask the Account Specialist. "
        f"Keep your responses friendly, polite, and very short, optimized for voice text-to-speech."
    )
    
    formatted_messages = [SystemMessage(content=system_instruction)] + list(messages)
    response = support_llm.invoke(formatted_messages)
    if hasattr(response, "usage_metadata"):
        log_token_usage("Support Specialist Agent", response.usage_metadata)
    
    return {
        "messages": [response],
        "active_agent_name": "Support Specialist"
    }

def tool_execution_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        print(f"Executing tool {tool_name} with args {tool_args}...")
        
        try:
            if tool_name == "get_transaction_history":
                result = get_transaction_history(**tool_args)
            elif tool_name == "send_money":
                result = send_money(**tool_args)
            elif tool_name == "get_fixed_deposit_details":
                result = get_fixed_deposit_details()
            elif tool_name == "get_balance":
                result = get_balance()
            else:
                result = f"Error: Tool {tool_name} not found."
        except Exception as e:
            result = f"Error executing tool: {str(e)}"
            
        tool_messages.append(ToolMessage(
            content=result,
            name=tool_name,
            tool_call_id=tool_call["id"]
        ))
        
    return {"messages": tool_messages}

# --- Routing Logic ---

def route_by_intent(state: AgentState):
    return state["next_agent"]

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tools"
    return "end"

def route_back(state: AgentState):
    agent_name = state.get("active_agent_name")
    if agent_name == "Fixed Deposit Specialist":
        return "fd"
    return "account"

# --- Construct the LangGraph workflow ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("account_agent", account_agent_node)
workflow.add_node("fd_agent", fd_agent_node)
workflow.add_node("support_agent", support_agent_node)
workflow.add_node("tool_execution_node", tool_execution_node)

# Set Entry Point
workflow.set_entry_point("router")

# Router conditional routing
workflow.add_conditional_edges(
    "router",
    route_by_intent,
    {
        "account": "account_agent",
        "fd": "fd_agent",
        "support": "support_agent"
    }
)

# Account Agent conditional routing (loop to tools if needed)
workflow.add_conditional_edges(
    "account_agent",
    should_continue,
    {
        "call_tools": "tool_execution_node",
        "end": END
    }
)

# Fixed Deposit Agent conditional routing (loop to tools if needed)
workflow.add_conditional_edges(
    "fd_agent",
    should_continue,
    {
        "call_tools": "tool_execution_node",
        "end": END
    }
)

# Support Agent has no tools, directly transitions to END
workflow.add_edge("support_agent", END)

# Tool execution loops back to the caller agent
workflow.add_conditional_edges(
    "tool_execution_node",
    route_back,
    {
        "account": "account_agent",
        "fd": "fd_agent"
    }
)

# Compile Workflow
agents_graph = workflow.compile()
