"""
config.py — Centralised config for the AI Customer Support Chatbot.
All credentials loaded from environment variables only.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── IBM watsonx.ai ────────────────────────────────────────────────────────
    WATSONX_API_KEY    = os.environ.get("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID = os.environ.get("WATSONX_PROJECT_ID", "280ea383-d47b-42ab-a981-b28f66296121")
    WATSONX_ENDPOINT   = os.environ.get("WATSONX_ENDPOINT", "https://au-syd.ml.cloud.ibm.com")
    WATSONX_MODEL_ID   = os.environ.get("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")
    IAM_TOKEN_URL      = "https://iam.cloud.ibm.com/identity/token"
    WATSONX_API_VER    = "2025-02-11"

    # ── LLM defaults ─────────────────────────────────────────────────────────
    MAX_TOKENS_REPLY   = 512
    MAX_TOKENS_SUMMARY = 300
    TEMPERATURE        = 0.5

    # ── Chatbot persona ───────────────────────────────────────────────────────
    BOT_NAME    = "Aria"
    COMPANY     = "IBM TechSupport"
    APP_TITLE   = "AI Customer Support — Powered by IBM watsonx.ai"
    APP_VERSION = "1.0.0"

    # ── Escalation trigger keywords ───────────────────────────────────────────
    ESCALATION_KEYWORDS = [
        "human", "agent", "representative", "manager", "supervisor",
        "speak to someone", "real person", "escalate", "urgent", "legal",
        "lawsuit", "refund not received", "fraud", "scam", "hacked",
    ]

    # ── Guardrail blocked topics ──────────────────────────────────────────────
    BLOCKED_TOPICS = [
        "hate speech", "violence", "self-harm", "illegal",
        "adult content", "personal data leak", "sql injection",
        "prompt injection", "jailbreak", "ignore previous instructions",
    ]

    # ── Predefined FAQ knowledge base ────────────────────────────────────────
    FAQ = {
        "What are your support hours?":
            "Our AI support is available 24/7. Human agents are available Mon–Fri, 9 AM–6 PM (EST).",
        "How do I reset my password?":
            "Visit the login page and click 'Forgot Password'. Enter your email and follow the reset link sent to your inbox.",
        "How do I track my order?":
            "Log in to your account and go to 'My Orders'. You'll find real-time tracking for all active shipments.",
        "What is your refund policy?":
            "We offer a 30-day no-questions-asked refund policy. Submit a refund request through your account dashboard.",
        "How do I cancel my subscription?":
            "Go to Account Settings → Subscriptions → Cancel. Your access will continue until the end of the billing period.",
        "How do I contact billing support?":
            "Email billing@ibmtechsupport.com or call 1-800-IBM-HELP (Mon–Fri, 9 AM–6 PM EST).",
        "Is my data secure?":
            "Yes. We use AES-256 encryption for all data at rest and TLS 1.3 for data in transit. We are SOC 2 Type II certified.",
        "How do I update my account details?":
            "Log in → Account Settings → Profile. You can update your name, email, and contact details there.",
    }
