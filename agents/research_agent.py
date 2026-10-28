"""
agents/research_agent.py
Fetches real-time articles from RSS feeds, extracts summaries,
and returns structured source-cited research results.
"""

import re
import feedparser
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from config import Config


def _clean(text: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = BeautifulSoup(text or "", "html.parser").get_text()
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss_articles(topic: str, max_per_feed: int = 3) -> list[dict]:
    """
    Query all configured RSS feeds and return articles
    whose title or summary mention the topic.
    """
    results = []
    topic_lower = topic.lower()
    for source, url in Config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title   = _clean(entry.get("title", ""))
                summary = _clean(entry.get("summary", entry.get("description", "")))
                link    = entry.get("link", "")
                pub     = entry.get("published", "")
                if topic_lower in title.lower() or topic_lower in summary.lower():
                    results.append({
                        "source":    source,
                        "title":     title,
                        "summary":   summary[:400],
                        "url":       link,
                        "published": pub,
                    })
                    if len([r for r in results if r["source"] == source]) >= max_per_feed:
                        break
        except Exception:
            continue
    return results[:20]


def fetch_top_headlines(max_articles: int = 10) -> list[dict]:
    """Return latest headlines across all feeds (no topic filter)."""
    results = []
    for source, url in Config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                results.append({
                    "source":    source,
                    "title":     _clean(entry.get("title", "")),
                    "summary":   _clean(entry.get("summary", ""))[:300],
                    "url":       entry.get("link", ""),
                    "published": entry.get("published", ""),
                })
        except Exception:
            continue
    return results[:max_articles]


def summarize_research(articles: list[dict], topic: str, llm) -> str:
    """Use LLM to synthesize a research summary from fetched articles."""
    if not articles:
        return f"No articles found for '{topic}'. Try a broader search term."

    snippets = "\n\n".join(
        f"[{i+1}] **{a['source']}** — {a['title']}\n{a['summary']}\nSource: {a['url']}"
        for i, a in enumerate(articles[:8])
    )

    system = (
        "You are a professional research analyst and fact-checker. "
        "Synthesize the provided articles into a concise, accurate research summary. "
        "Cite sources by their number [1], [2] etc. "
        "Do not fabricate facts. Be objective and balanced."
    )
    user_msg = (
        f"Topic: {topic}\n\n"
        f"Articles:\n{snippets}\n\n"
        "Write a 250-300 word research summary with key findings, "
        "notable trends, and source citations."
    )
    return llm.ask(system, user_msg, max_tokens=500)
