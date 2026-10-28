"""
config.py — Central configuration for the Blogging Assistant.
All secrets are loaded from environment variables / .env file only.
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

    # ── LLM generation defaults ───────────────────────────────────────────────
    DEFAULT_MAX_TOKENS = 1500
    CHAT_MAX_TOKENS    = 600

    # ── RSS / news feeds (no auth required) ──────────────────────────────────
    RSS_FEEDS = {
        "TechCrunch":      "https://techcrunch.com/feed/",
        "Wired":           "https://www.wired.com/feed/rss",
        "MIT Tech Review": "https://www.technologyreview.com/feed/",
        "HackerNews":      "https://hnrss.org/frontpage",
        "Dev.to":          "https://dev.to/feed",
        "Medium Tech":     "https://medium.com/feed/topic/technology",
        "The Verge":       "https://www.theverge.com/rss/index.xml",
    }

    # ── Guardrails ────────────────────────────────────────────────────────────
    BLOCKED_KEYWORDS = [
        "hate speech", "violence", "self-harm", "illegal",
        "misinformation", "spam", "plagiarism", "adult content",
    ]

    # ── App meta ──────────────────────────────────────────────────────────────
    APP_NAME    = "Writing Pulse — AI Blogging Assistant"
    APP_VERSION = "1.0.0"
