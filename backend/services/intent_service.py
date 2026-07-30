import re
import difflib
import random

# ---------------------------------------------------------------------------
# Templates & Dictionaries
# ---------------------------------------------------------------------------

GREETING_TEMPLATES = [
    "Hello! I'm Dr. Khare's AI Assistant. How can I help you today?",
    "Hi there! I'm the AI Assistant for Dr. Khare. What would you like to know?",
    "Greetings! I'm Dr. Khare's AI Assistant. How can I assist you?",
    "Hello! How can I help you learn more about Dr. Khare today?",
    "Hi! I'm here to answer your questions about Dr. Khare. What's on your mind?",
    "Welcome! I am Dr. Khare's AI Assistant. How can I be of service?",
]

EXACT_GREETINGS = {
    "hello", "hi", "hii", "hiii", "hiiii", "hey", "heyy", "heyyy", "helo", "helloo", "hlo", "hy",
    "yo", "sup", "wassup", "whats up", "what's up", "gm", "good morning", "gud morning", 
    "good afternoon", "good evening", "namaste", "namaskar", "jai shree ram", "ram ram", "salaam", "greetings"
}

# Typos target strings
FUZZY_TARGETS = list(EXACT_GREETINGS)

SMALL_TALK = {
    "how are you": "I'm doing well, thank you! I'm Dr. Khare's AI Assistant. I can answer questions about Dr. Khare's education, research, work experience, publications, certifications, and professional background.",
    "who are you": "I'm Dr. Khare's AI Assistant. I can answer questions about Dr. Khare's education, research, work experience, publications, certifications, and professional background.",
    "what can you do": "I'm Dr. Khare's AI Assistant. I can answer questions about Dr. Khare's education, research, work experience, publications, certifications, and professional background.",
    "help": "I'm Dr. Khare's AI Assistant. I can answer questions about Dr. Khare's education, research, work experience, publications, certifications, and professional background.",
    "thank you": "You're welcome! Let me know if you have any more questions about Dr. Khare.",
    "thankyou": "You're welcome! Let me know if you have any more questions about Dr. Khare.",
    "thanks": "You're welcome! Let me know if you have any more questions about Dr. Khare.",
    "okay": "Sure! What else would you like to know?",
    "ok": "Sure! What else would you like to know?",
    "bye": "Goodbye! Feel free to come back anytime.",
    "goodbye": "Goodbye! Feel free to come back anytime.",
    "see you": "See you later! Come back if you have more questions.",
    "take care": "Take care! Have a great day.",
    "tc": "Take care! Have a great day."
}

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def _normalize(query: str) -> str:
    """Lowercase and strip leading/trailing whitespace, remove basic punctuation at the end."""
    q = query.lower().strip()
    q = re.sub(r'[!?.,;:]+$', '', q)
    return q

def _remove_names(query: str) -> str:
    """Remove target names like 'dr khare' or 'assistant' to check if the remainder is a greeting."""
    removals = ["dr khare", "dr. khare", "assistant", "bot", "ai", "supreet khare", "dr supreet khare"]
    q = query
    for r in removals:
        q = q.replace(r, "")
    return q.strip()

def detect_intent(query: str) -> tuple[str | None, str | None]:
    """
    Detects if the query is a Greeting or Small Talk.
    Returns (Intent, Response). If no intent matched, returns (None, None).
    """
    norm_q = _normalize(query)
    
    # 1. Exact Match Small Talk
    if norm_q in SMALL_TALK:
        if norm_q == "help":
            return "Help", SMALL_TALK[norm_q]
        return "Small Talk", SMALL_TALK[norm_q]
        
    # Also check if it starts with small talk (e.g. "thanks a lot")
    for st_key in ["thanks", "thank you", "bye", "goodbye", "how are you", "who are you"]:
        if norm_q.startswith(st_key):
            return "Small Talk", SMALL_TALK[st_key]

    # 2. Extract potential greeting by stripping names
    stripped_q = _remove_names(norm_q)
    
    # 3. Exact Match Greeting
    if norm_q in EXACT_GREETINGS or stripped_q in EXACT_GREETINGS:
        return "Greeting", random.choice(GREETING_TEMPLATES)
        
    # 4. Fuzzy Match Greeting
    # Use cutoff=0.8 to tolerate common typos (e.g. "helllo", "namste")
    # difflib.get_close_matches is extremely fast for small lists like FUZZY_TARGETS
    # Check both the normalized full query and the stripped query
    if len(norm_q) <= 20: # Don't fuzzy match long paragraphs
        matches = difflib.get_close_matches(norm_q, FUZZY_TARGETS, n=1, cutoff=0.80)
        if matches:
            return "Greeting", random.choice(GREETING_TEMPLATES)
            
        if stripped_q and len(stripped_q) <= 20:
            matches_stripped = difflib.get_close_matches(stripped_q, FUZZY_TARGETS, n=1, cutoff=0.80)
            if matches_stripped:
                return "Greeting", random.choice(GREETING_TEMPLATES)

    return None, None
