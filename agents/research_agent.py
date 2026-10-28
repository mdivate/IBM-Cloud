"""
agents/research_agent.py — Research Agent
=========================================
Fetches real-time articles from RSS feeds and news sources,
extracts clean article text, builds source-cited research summaries,
and provides structured citations for blog generation.

Capabilities:
  • fetch_rss_articles(topic)     — topic-filtered article search
  • fetch_top_headlines()         — latest news across all feeds
  • summarize_research(articles, topic, llm) — AI synthesis with citations
  • format_citations(articles)    — APA-style in-line citation list
"""

import re
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config


# ── Text utilities ─────────────────────────────────────────────────────────────

def _clean(text: str, max_len: int = 500) -> str:
    """Strip HTML/XML, collapse whitespace, truncate."""
    soup = BeautifulSoup(text or "", "html.parser")
    clean = re.sub(r"\s+", " ", soup.get_text()).strip()
    return clean[:max_len]


def _parse_date(entry) -> str:
    """Best-effort published date extraction from a feedparser entry."""
    for attr in ("published", "updated", "created"):
        val = getattr(entry, attr, None) or entry.get(attr, "")
        if val:
            return str(val)
    return "Unknown date"


def _topic_matches(topic: str, title: str, summary: str) -> bool:
    """True when at least one word in the topic appears in title or summary."""
    words = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 2]
    combined = (title + " " + summary).lower()
    return any(w in combined for w in words)


# ── Core feed functions ────────────────────────────────────────────────────────

def fetch_rss_articles(topic: str, max_per_feed: int = 3) -> list[dict]:
    """
    Search all configured RSS feeds for articles related to *topic*.
    Returns up to 20 structured article dicts with source citations.
    """
    results: list[dict] = []

    for source, url in Config.RSS_FEEDS.items():
        count = 0
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title   = _clean(entry.get("title", ""), 200)
                summary = _clean(
                    entry.get("summary", entry.get("description", "")), 500
                )
                link    = entry.get("link", "")
                pub     = _parse_date(entry)

                if _topic_matches(topic, title, summary):
                    results.append({
                        "source":    source,
                        "title":     title,
                        "summary":   summary,
                        "url":       link,
                        "published": pub,
                    })
                    count += 1
                    if count >= max_per_feed:
                        break
        except Exception:
            continue

    return results[:25]


def fetch_top_headlines(max_articles: int = 12) -> list[dict]:
    """
    Return the latest headlines across all configured feeds.
    No topic filtering — good for dashboard discovery.
    """
    results: list[dict] = []
    seen_titles: set[str] = set()

    for source, url in Config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = _clean(entry.get("title", ""), 200)
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    results.append({
                        "source":    source,
                        "title":     title,
                        "summary":   _clean(
                            entry.get("summary", entry.get("description", "")),
                            300,
                        ),
                        "url":       entry.get("link", ""),
                        "published": _parse_date(entry),
                    })
        except Exception:
            continue

    return results[:max_articles]


# ── AI research synthesis ──────────────────────────────────────────────────────

def summarize_research(articles: list[dict], topic: str, llm) -> str:
    """
    Synthesize a structured research summary from fetched articles using the LLM.
    Includes numbered source citations [1], [2], …
    """
    if not articles:
        return (
            f"No articles found for **'{topic}'**. "
            "Try broader or different search terms."
        )

    snippets = "\n\n".join(
        f"[{i+1}] **{a['source']}** — {a['title']}\n"
        f"    {a['summary'][:350]}\n"
        f"    URL: {a['url']}"
        for i, a in enumerate(articles[:10])
    )

    system = (
        "You are a professional research analyst, fact-checker, and journalist. "
        "Your task is to synthesize multiple news articles into a concise, "
        "well-structured research summary. "
        "Rules: cite sources by their bracketed number [1][2]. "
        "Do NOT fabricate any facts or statistics. "
        "Be objective, balanced, and precise. "
        "Highlight key trends, conflicting perspectives (if any), and "
        "the most newsworthy insights."
    )
    user_msg = (
        f"Topic: **{topic}**\n\n"
        f"Source articles:\n{snippets}\n\n"
        "Write a 280–350 word research summary covering:\n"
        "1. Key findings and recent developments\n"
        "2. Emerging trends\n"
        "3. Notable expert opinions or data points (cite sources)\n"
        "4. A one-sentence 'So what?' takeaway for a blog writer\n\n"
        "Always cite sources as [1], [2], etc."
    )
    return llm.ask(system, user_msg, max_tokens=Config.RESEARCH_MAX_TOKENS, temperature=0.45)


# ── Citation formatter ─────────────────────────────────────────────────────────

def format_citations(articles: list[dict]) -> str:
    """
    Return a Markdown reference list (APA-style) for displaying
    at the end of a generated blog post.
    """
    if not articles:
        return ""

    lines = []
    for i, a in enumerate(articles[:10], start=1):
        pub = a.get("published", "n.d.")
        # Keep only first 60 chars of date string for readability
        pub_short = str(pub)[:30] if pub else "n.d."
        lines.append(
            f"[{i}] {a['source']}. *{a['title']}*. "
            f"Retrieved {pub_short}. [{a['url']}]({a['url']})"
        )

    return "\n\n**References:**\n\n" + "\n\n".join(lines)
