"""
agents/trend_agent.py — Trend Analysis Agent
=============================================
Analyzes trending topics from live news feeds, suggests SEO blog topics,
predicts engagement scores, recommends optimal publishing windows, and
generates hashtag sets using IBM Granite via watsonx.ai.

Capabilities:
  • get_trending_topics()            — keyword frequency ranking from RSS
  • suggest_blog_topics(trending, llm) — AI-generated topic ideas
  • predict_engagement(topic, llm)   — engagement score + best publish window
  • get_topic_heatmap(trending)      — data for visualisation
"""

import re
from collections import Counter
import feedparser
from config import Config


# ── Keyword extraction ─────────────────────────────────────────────────────────

_STOP = Config.SEO_STOP_WORDS | {
    "says", "said", "new", "year", "day", "time", "just", "like",
    "make", "made", "take", "took", "want", "need", "know", "show",
    "could", "would", "should", "come", "going", "using", "used",
    "getting", "look", "looking", "first", "last", "next", "back",
    "even", "still", "around", "much", "many", "every", "while",
}


def _extract_keywords(text: str, top_n: int = 20) -> list[tuple[str, int]]:
    """Extract top keywords from text, excluding stop-words."""
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    filtered = [w for w in words if w not in _STOP]
    return Counter(filtered).most_common(top_n)


def _bigrams(text: str) -> list[str]:
    """Extract meaningful two-word phrases from text."""
    words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", text.lower()) if w not in _STOP]
    pairs = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    return pairs


# ── Trending topics ────────────────────────────────────────────────────────────

def get_trending_topics(max_feeds: int = 8) -> list[dict]:
    """
    Aggregate article titles from RSS feeds, rank keywords by frequency,
    and return the top trending topics with supporting headlines.

    Each returned dict: { keyword, count, headlines, feed_sources }
    """
    all_titles: list[str] = []
    feed_data: dict[str, list[str]] = {}
    feed_sources: dict[str, list[str]] = {}  # keyword → [source names]

    for source, url in list(Config.RSS_FEEDS.items())[:max_feeds]:
        try:
            feed = feedparser.parse(url)
            titles = [
                e.get("title", "")
                for e in feed.entries[:12]
                if e.get("title")
            ]
            feed_data[source] = titles
            all_titles.extend(titles)
        except Exception:
            continue

    combined = " ".join(all_titles)
    kw_counts = _extract_keywords(combined, top_n=20)

    topics: list[dict] = []
    for kw, cnt in kw_counts:
        matching_titles = [t for t in all_titles if kw in t.lower()][:4]
        sources = [
            src for src, titles in feed_data.items()
            if any(kw in t.lower() for t in titles)
        ]
        if matching_titles:
            topics.append({
                "keyword":      kw,
                "count":        cnt,
                "headlines":    matching_titles,
                "feed_sources": sources,
            })

    topics.sort(key=lambda x: x["count"], reverse=True)
    return topics[:12]


def get_topic_heatmap(trending: list[dict]) -> list[dict]:
    """
    Return keyword frequency data suitable for a Plotly bar/treemap chart.
    """
    return [
        {"keyword": t["keyword"], "count": t["count"]}
        for t in trending
    ]


# ── AI blog topic suggestions ──────────────────────────────────────────────────

def suggest_blog_topics(trending: list[dict], llm) -> list[dict]:
    """
    Use IBM Granite to generate 5 compelling, SEO-friendly blog topics
    from the trending keywords.

    Each returned dict: { title, description, audience, hashtags, angle }
    """
    if not trending:
        return []

    kw_list = ", ".join(t["keyword"] for t in trending[:10])
    system = (
        "You are an expert blog strategist, SEO specialist, and content marketer. "
        "Your task is to generate creative, data-driven, SEO-optimised blog topic ideas "
        "based on trending keywords. Focus on relevance, reader value, and search intent. "
        "Each topic should have a compelling angle that differentiates it from generic posts."
    )
    user_msg = (
        f"Trending keywords right now: {kw_list}\n\n"
        "Generate 5 unique, high-engagement blog topic ideas. "
        "Format EXACTLY as (repeat for each topic):\n\n"
        "**Title:** [catchy, SEO-optimised headline under 65 chars]\n"
        "**Description:** [one sentence describing the post value]\n"
        "**Audience:** [specific target reader persona]\n"
        "**Angle:** [what makes this post unique / differentiating]\n"
        "**Hashtags:** #tag1 #tag2 #tag3 #tag4 #tag5\n"
        "---"
    )
    raw = llm.ask(system, user_msg, max_tokens=Config.SUGGEST_MAX_TOKENS, temperature=0.85)

    suggestions: list[dict] = []
    blocks = [b.strip() for b in raw.split("---") if b.strip()]
    for block in blocks[:6]:
        s: dict = {
            "title": "", "description": "", "audience": "",
            "angle": "", "hashtags": [],
        }
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("**Title:**"):
                s["title"] = line.replace("**Title:**", "").strip()
            elif line.startswith("**Description:**"):
                s["description"] = line.replace("**Description:**", "").strip()
            elif line.startswith("**Audience:**"):
                s["audience"] = line.replace("**Audience:**", "").strip()
            elif line.startswith("**Angle:**"):
                s["angle"] = line.replace("**Angle:**", "").strip()
            elif line.startswith("**Hashtags:**"):
                raw_tags = line.replace("**Hashtags:**", "").strip()
                s["hashtags"] = [
                    t.strip() for t in raw_tags.split()
                    if t.startswith("#")
                ]
        if s["title"]:
            suggestions.append(s)

    return suggestions


# ── Engagement prediction ──────────────────────────────────────────────────────

def predict_engagement(topic: str, llm) -> dict:
    """
    Predict engagement potential (0–100), best publish day/time, top hashtags,
    and estimated reach for a given blog topic.

    Uses IBM Granite for qualitative analysis + Config.PUBLISH_WINDOWS
    for evidence-based timing recommendations.
    """
    system = (
        "You are a digital marketing analyst specialising in content performance. "
        "Analyse blog topics and predict audience engagement metrics based on "
        "content type, timeliness, search demand, and social sharing patterns. "
        "Be data-driven and specific."
    )
    user_msg = (
        f"Blog topic: '{topic}'\n\n"
        "Predict engagement and respond ONLY in this exact format "
        "(no extra text before or after):\n"
        "Score: [0-100]\n"
        "Best Day: [day of week, e.g. Wednesday]\n"
        "Best Time: [e.g. 9:00 AM AEST]\n"
        "Reason: [one sentence explaining the score]\n"
        "Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5\n"
        "Reach: [Low / Medium / High / Viral]\n"
        "Content Type: [e.g. How-to, Opinion, Data-driven, Trend analysis]"
    )
    raw = llm.ask(system, user_msg, max_tokens=Config.ENGAGE_MAX_TOKENS, temperature=0.5)

    result: dict = {
        "score":        70,
        "best_day":     "Wednesday",
        "best_time":    "9:00 AM",
        "reason":       "",
        "hashtags":     [],
        "reach":        "Medium",
        "content_type": "Informational",
    }

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("Score:"):
            m = re.search(r"\d+", line)
            if m:
                result["score"] = min(100, max(0, int(m.group())))
        elif line.startswith("Best Day:"):
            result["best_day"] = line.replace("Best Day:", "").strip()
        elif line.startswith("Best Time:"):
            result["best_time"] = line.replace("Best Time:", "").strip()
        elif line.startswith("Reason:"):
            result["reason"] = line.replace("Reason:", "").strip()
        elif line.startswith("Hashtags:"):
            raw_tags = line.replace("Hashtags:", "").strip()
            result["hashtags"] = [
                t.strip() for t in raw_tags.split()
                if t.startswith("#")
            ]
        elif line.startswith("Reach:"):
            result["reach"] = line.replace("Reach:", "").strip()
        elif line.startswith("Content Type:"):
            result["content_type"] = line.replace("Content Type:", "").strip()

    # Blend LLM score with our evidence-based publish window data
    day_data = Config.PUBLISH_WINDOWS.get(result["best_day"], {})
    if day_data:
        base = day_data["base_score"]
        result["score"] = int(result["score"] * 0.65 + base * 0.35)
        # Override time only if LLM didn't provide a specific time
        if not result["best_time"] or result["best_time"] == "9:00 AM":
            result["best_time"] = day_data["best_time"]

    return result
