"""
core/chatbot_engine.py
Core chatbot logic:
  - Guardrail filtering
  - FAQ matching
  - Intent detection (billing / technical / general / escalation)
  - Sentiment analysis (lexicon-based, no ML deps)
  - Ticket generation
  - Conversation summarisation
  - Full AI response with multi-turn context
"""

import re
import uuid
from datetime import datetime
from config import Config

# ── Sentiment lexicons ────────────────────────────────────────────────────────
_POS = {
    "thanks","thank","great","excellent","perfect","helpful","good","awesome",
    "brilliant","love","happy","satisfied","amazing","wonderful","appreciate",
    "resolved","fixed","solved","works","working","pleased","clear","fast",
}
_NEG = {
    "bad","terrible","awful","frustrated","angry","upset","broken","failed",
    "wrong","useless","disappointed","hate","worst","stuck","error","issue",
    "problem","cant","cannot","doesnt","wont","never","slow","crash","bug",
    "refund","complaint","unacceptable","ridiculous","waste",
}


def analyze_sentiment(text: str) -> dict:
    """Lexicon-based sentiment analysis. Returns label, score, emoji."""
    words = re.findall(r"\b\w+\b", text.lower())
    pos = sum(1 for w in words if w in _POS)
    neg = sum(1 for w in words if w in _NEG)
    total = pos + neg or 1
    score = round((pos - neg) / total, 2)

    if score > 0.15:
        return {"label": "Positive", "score": score, "emoji": "😊", "color": "#24a148"}
    elif score < -0.15:
        return {"label": "Negative", "score": score, "emoji": "😟", "color": "#da1e28"}
    else:
        return {"label": "Neutral",  "score": score, "emoji": "😐", "color": "#8d8d8d"}


# ── Guardrails ────────────────────────────────────────────────────────────────

def guardrail_check(text: str) -> tuple[bool, str]:
    """Returns (is_safe, warning_msg)."""
    lower = text.lower()
    for kw in Config.BLOCKED_TOPICS:
        if kw in lower:
            return False, (
                f"I'm sorry, I can't process that request. "
                f"Please keep queries related to customer support. "
                f"If you need further assistance, type 'speak to an agent'."
            )
    return True, ""


# ── FAQ matching ──────────────────────────────────────────────────────────────

def match_faq(user_input: str) -> str | None:
    """
    Simple keyword-based FAQ lookup.
    Returns the answer string if a match is found, else None.
    """
    lower = user_input.lower()
    # Direct keyword triggers
    faq_triggers = {
        "password":                 Config.FAQ["How do I reset my password?"],
        "reset":                    Config.FAQ["How do I reset my password?"],
        "track" :                   Config.FAQ["How do I track my order?"],
        "order":                    Config.FAQ["How do I track my order?"],
        "refund":                   Config.FAQ["What is your refund policy?"],
        "return":                   Config.FAQ["What is your refund policy?"],
        "cancel":                   Config.FAQ["How do I cancel my subscription?"],
        "subscription":             Config.FAQ["How do I cancel my subscription?"],
        "billing":                  Config.FAQ["How do I contact billing support?"],
        "invoice":                  Config.FAQ["How do I contact billing support?"],
        "secure":                   Config.FAQ["Is my data secure?"],
        "security":                 Config.FAQ["Is my data secure?"],
        "data":                     Config.FAQ["Is my data secure?"],
        "update account":           Config.FAQ["How do I update my account details?"],
        "account details":          Config.FAQ["How do I update my account details?"],
        "support hours":            Config.FAQ["What are your support hours?"],
        "hours":                    Config.FAQ["What are your support hours?"],
        "available":                Config.FAQ["What are your support hours?"],
    }
    for keyword, answer in faq_triggers.items():
        if keyword in lower:
            return answer
    return None


# ── Intent detection ──────────────────────────────────────────────────────────

def detect_intent(text: str) -> str:
    """
    Classify user message into one of:
    escalation | billing | technical | account | general
    """
    lower = text.lower()
    if any(kw in lower for kw in Config.ESCALATION_KEYWORDS):
        return "escalation"
    if any(w in lower for w in ["bill","invoice","charge","payment","price","cost","refund","cancel"]):
        return "billing"
    if any(w in lower for w in ["error","bug","crash","not working","broken","fail","install","setup","configure","api","code"]):
        return "technical"
    if any(w in lower for w in ["account","login","password","profile","username","email","2fa","mfa"]):
        return "account"
    return "general"


# ── Ticket generation ─────────────────────────────────────────────────────────

def generate_ticket(user_name: str, issue_summary: str, intent: str, sentiment: dict) -> dict:
    """Create a support ticket dict."""
    return {
        "ticket_id":    f"TKT-{uuid.uuid4().hex[:8].upper()}",
        "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer":     user_name or "Guest",
        "intent":       intent.capitalize(),
        "summary":      issue_summary[:200],
        "sentiment":    sentiment["label"],
        "priority":     "High" if sentiment["label"] == "Negative" else "Normal",
        "status":       "Open",
    }


# ── System prompt builder ─────────────────────────────────────────────────────

def build_system_prompt(intent: str, user_name: str) -> str:
    name_clause = f"The customer's name is {user_name}. " if user_name else ""
    base = (
        f"You are {Config.BOT_NAME}, a friendly, professional, and empathetic AI customer support agent for {Config.COMPANY}. "
        f"{name_clause}"
        "Your goals:\n"
        "1. Resolve customer issues efficiently and accurately.\n"
        "2. Be polite, concise, and helpful at all times.\n"
        "3. If you don't know the answer, say so honestly and offer to escalate.\n"
        "4. Never fabricate information or make promises you cannot keep.\n"
        "5. Always end with 'Is there anything else I can help you with?'\n"
        "6. Keep responses under 150 words unless a detailed technical explanation is needed.\n"
    )
    intent_hints = {
        "billing":    "This is a billing inquiry. Be extra careful, confirm details before making statements about charges.",
        "technical":  "This is a technical support issue. Provide step-by-step troubleshooting guidance.",
        "account":    "This is an account management issue. Guide the customer through the steps clearly.",
        "escalation": "The customer wants to speak to a human agent. Acknowledge this, collect their issue details, and let them know a human agent will follow up.",
        "general":    "This is a general inquiry. Be helpful and friendly.",
    }
    return base + "\n" + intent_hints.get(intent, "")


# ── Conversation summariser ───────────────────────────────────────────────────

def summarize_conversation(conversation: list[dict], llm) -> str:
    """Generate a brief summary of the conversation for ticket notes."""
    if not conversation:
        return "No conversation recorded."

    transcript = "\n".join(
        f"{'Customer' if t['role']=='user' else 'Agent'}: {t['content']}"
        for t in conversation[-12:]
    )
    system = (
        "You are a support ticket assistant. "
        "Summarize the following customer support conversation in 2-3 sentences. "
        "Mention the main issue, what was resolved, and any open action items."
    )
    user_msg = f"Conversation:\n{transcript}\n\nWrite a brief summary."
    prompt = (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n\n"
        f"{system}<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg}<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    return llm.generate(prompt, max_tokens=Config.MAX_TOKENS_SUMMARY, temperature=0.4)


# ── Main response handler ─────────────────────────────────────────────────────

def get_bot_response(
    user_msg: str,
    conversation: list[dict],
    user_name: str,
    llm,
) -> dict:
    """
    Full pipeline:
    guardrail → FAQ → intent → AI response
    Returns dict with: reply, intent, sentiment, faq_matched, escalate
    """
    # 1. Guardrail
    safe, warning = guardrail_check(user_msg)
    if not safe:
        return {
            "reply":       warning,
            "intent":      "blocked",
            "sentiment":   analyze_sentiment(user_msg),
            "faq_matched": False,
            "escalate":    False,
        }

    sentiment = analyze_sentiment(user_msg)
    intent    = detect_intent(user_msg)

    # 2. Escalation shortcut
    if intent == "escalation":
        reply = (
            f"I completely understand, {user_name or 'valued customer'}. "
            "I've flagged your request for a human agent. "
            "A support representative will reach out to you within 1 business hour. "
            "Could you briefly describe your issue so I can include it in the handoff notes?"
        )
        return {
            "reply":       reply,
            "intent":      intent,
            "sentiment":   sentiment,
            "faq_matched": False,
            "escalate":    True,
        }

    # 3. FAQ match
    faq_answer = match_faq(user_msg)
    if faq_answer:
        reply = (
            f"{faq_answer}\n\n"
            "Is there anything else I can help you with?"
        )
        return {
            "reply":       reply,
            "intent":      intent,
            "sentiment":   sentiment,
            "faq_matched": True,
            "escalate":    False,
        }

    # 4. LLM response
    system = build_system_prompt(intent, user_name)
    try:
        reply = llm.chat(
            system=system,
            conversation=conversation,
            user_msg=user_msg,
            max_tokens=Config.MAX_TOKENS_REPLY,
            temperature=Config.TEMPERATURE,
        )
    except Exception as e:
        reply = (
            "I apologise, I'm having trouble connecting to the AI service right now. "
            "Please try again in a moment, or type 'speak to an agent' to reach our team. "
            f"(Error: {str(e)[:80]})"
        )

    return {
        "reply":       reply,
        "intent":      intent,
        "sentiment":   sentiment,
        "faq_matched": False,
        "escalate":    False,
    }
