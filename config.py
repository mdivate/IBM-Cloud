"""
config.py — Central configuration for Writing Pulse AI Blogging Assistant.
All secrets loaded from environment variables / .env file only.
Never hard-code credentials in source files.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── IBM watsonx.ai / Granite ──────────────────────────────────────────────
    WATSONX_API_KEY    = os.environ.get("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID = os.environ.get("WATSONX_PROJECT_ID", "280ea383-d47b-42ab-a981-b28f66296121")
    WATSONX_ENDPOINT   = os.environ.get("WATSONX_ENDPOINT",  "https://au-syd.ml.cloud.ibm.com")
    # Primary: IBM Granite 3.3 8B Instruct — if unavailable, falls back to Llama 3.3 70B
    WATSONX_MODEL_ID   = os.environ.get("WATSONX_MODEL_ID",  "ibm/granite-3-3-8b-instruct")
    WATSONX_FALLBACK_MODEL = "meta-llama/llama-3-3-70b-instruct"
    IAM_TOKEN_URL      = "https://iam.cloud.ibm.com/identity/token"
    WATSONX_API_VER    = "2025-02-11"

    # ── LLM generation parameters ─────────────────────────────────────────────
    DEFAULT_MAX_TOKENS   = 1500
    CHAT_MAX_TOKENS      = 600
    DRAFT_MAX_TOKENS     = 2500
    REVIEW_MAX_TOKENS    = 700
    SOCIAL_MAX_TOKENS    = 450
    ENGAGE_MAX_TOKENS    = 220
    RESEARCH_MAX_TOKENS  = 550
    SUGGEST_MAX_TOKENS   = 750

    # ── RSS / News feeds (public, no auth) ───────────────────────────────────
    RSS_FEEDS = {
        "TechCrunch":         "https://techcrunch.com/feed/",
        "Wired":              "https://www.wired.com/feed/rss",
        "MIT Tech Review":    "https://www.technologyreview.com/feed/",
        "HackerNews Top":     "https://hnrss.org/frontpage",
        "Dev.to":             "https://dev.to/feed",
        "The Verge":          "https://www.theverge.com/rss/index.xml",
        "Ars Technica":       "https://feeds.arstechnica.com/arstechnica/index",
        "VentureBeat":        "https://venturebeat.com/feed/",
        "InfoQ":              "https://www.infoq.com/feed/?utm_source=infoq&utm_medium=feed&utm_campaign=feed",
        "ZDNet":              "https://www.zdnet.com/news/rss.xml",
    }

    # ── Guardrails — blocked topic/content categories ────────────────────────
    BLOCKED_KEYWORDS = [
        "hate speech", "racial slur", "violence", "gore", "self-harm",
        "suicide instructions", "illegal weapons", "drug synthesis",
        "misinformation", "deepfake", "spam", "plagiarism",
        "adult content", "sexually explicit", "terrorism",
        "doxing", "personal attacks",
    ]

    # ── SEO helpers ───────────────────────────────────────────────────────────
    SEO_STOP_WORDS = {
        "the","a","an","and","or","but","in","on","at","to","for","of",
        "with","is","are","was","were","be","been","has","have","had",
        "this","that","it","its","from","by","as","up","not","we","you",
        "i","he","she","they","will","can","may","do","how","what","who",
        "why","when","where","which","your","our","their","about","into",
        "than","then","also","just","more","some","over","after","before",
    }

    # ── Engagement model — day/time scoring weights (0–100) ──────────────────
    PUBLISH_WINDOWS = {
        "Monday":    {"best_time": "8:00 AM",  "base_score": 72},
        "Tuesday":   {"best_time": "9:00 AM",  "base_score": 85},
        "Wednesday": {"best_time": "10:00 AM", "base_score": 88},
        "Thursday":  {"best_time": "9:00 AM",  "base_score": 83},
        "Friday":    {"best_time": "11:00 AM", "base_score": 74},
        "Saturday":  {"best_time": "9:00 AM",  "base_score": 60},
        "Sunday":    {"best_time": "11:00 AM", "base_score": 55},
    }

    # ── App metadata ──────────────────────────────────────────────────────────
    APP_NAME    = "Writing Pulse — Agentic AI Blogging Assistant"
    APP_VERSION = "2.0.0"
    APP_TAGLINE = (
        "Powered by IBM watsonx.ai · IBM Granite · "
        "Agentic Research, Content & Editorial AI"
    )
