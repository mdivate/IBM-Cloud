"""
agents/trend_agent.py
Analyzes trending topics from news feeds, suggests blog topics,
predicts engagement scores, optimal publish times, and hashtags.
"""

from collections import Counter
import re
import feedparser
from config import Config


# Common stop-words to ignore in keyword extraction
_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","has","have","had","this","that",
    "it","its","from","by","as","up","not","we","you","i","he","she","they",
    "will","can","may","do","how","what","who","why","when","where","which",
}


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    """Extract top keywords from text."""
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    filtered = [w for w in words if w not in _STOPWORDS]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def get_trending_topics(max_feeds: int = 5) -> list[dict]:
    """
    Aggregate titles from all RSS feeds, rank by keyword frequency,
    and return the top trending topics with supporting headlines.
    """
    all_titles: list[str] = []
    feed_data: dict[str, list[str]] = {}

    for source, url in list(Config.RSS_FEEDS.items())[:max_feeds]:
        try:
            feed = feedparser.parse(url)
            titles = [e.get("title", "") for e in feed.entries[:10]]
            feed_data[source] = titles
            all_titles.extend(titles)
        except Exception:
            continue

    combined_text = " ".join(all_titles)
    keywords = extract_keywords(combined_text, top_n=15)

    # Build topic objects: keyword + matching headlines
    topics = []
    for kw in keywords:
        matching = [t for t in all_titles if kw in t.lower()][:3]
        if matching:
            topics.append({
                "keyword":   kw,
                "count":     sum(1 for t in all_titles if kw in t.lower()),
                "headlines": matching,
            })

    topics.sort(key=lambda x: x["count"], reverse=True)
    return topics[:10]


def suggest_blog_topics(trending: list[dict], llm) -> list[dict]:
    """
    Use LLM to turn trending keywords into compelling,
    SEO-friendly blog topic suggestions.
    """
    if not trending:
        return []

    kw_list = ", ".join(t["keyword"] for t in trending[:8])
    system = (
        "You are an expert blog strategist and SEO specialist. "
        "Generate creative, compelling, and SEO-friendly blog topic ideas "
        "based on trending keywords. For each topic provide a catchy title, "
        "one-sentence description, target audience, and 5 relevant hashtags."
    )
    user_msg = (
        f"Trending keywords right now: {kw_list}\n\n"
        "Suggest 5 unique, high-engagement blog topics. "
        "Format each as:\n"
        "**Title:** [catchy SEO title]\n"
        "**Description:** [one sentence]\n"
        "**Audience:** [target reader]\n"
        "**Hashtags:** #tag1 #tag2 #tag3 #tag4 #tag5\n"
        "---"
    )
    raw = llm.ask(system, user_msg, max_tokens=700, temperature=0.85)

    # Parse the LLM output into structured dicts
    suggestions = []
    blocks = [b.strip() for b in raw.split("---") if b.strip()]
    for block in blocks[:5]:
        s = {"title": "", "description": "", "audience": "", "hashtags": []}
        for line in block.splitlines():
            if line.startswith("**Title:**"):
                s["title"] = line.replace("**Title:**", "").strip()
            elif line.startswith("**Description:**"):
                s["description"] = line.replace("**Description:**", "").strip()
            elif line.startswith("**Audience:**"):
                s["audience"] = line.replace("**Audience:**", "").strip()
            elif line.startswith("**Hashtags:**"):
                s["hashtags"] = line.replace("**Hashtags:**", "").strip().split()
        if s["title"]:
            suggestions.append(s)

    return suggestions


def predict_engagement(topic: str, llm) -> dict:
    """
    Predict engagement score (0-100), best publish day/time,
    and top hashtags for a given blog topic.
    """
    system = (
        "You are a digital marketing analyst specializing in blog performance. "
        "Analyze topics and predict engagement metrics."
    )
    user_msg = (
        f"Blog topic: '{topic}'\n\n"
        "Predict the following and respond ONLY in this exact format:\n"
        "Score: [0-100]\n"
        "Best Day: [day of week]\n"
        "Best Time: [time with timezone, e.g. 9:00 AM EST]\n"
        "Reason: [one sentence why]\n"
        "Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5"
    )
    raw = llm.ask(system, user_msg, max_tokens=200, temperature=0.5)

    result = {
        "score": 70, "best_day": "Tuesday", "best_time": "9:00 AM",
        "reason": "", "hashtags": []
    }
    for line in raw.splitlines():
        if line.startswith("Score:"):
            try:
                result["score"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line.startswith("Best Day:"):
            result["best_day"] = line.replace("Best Day:", "").strip()
        elif line.startswith("Best Time:"):
            result["best_time"] = line.replace("Best Time:", "").strip()
        elif line.startswith("Reason:"):
            result["reason"] = line.replace("Reason:", "").strip()
        elif line.startswith("Hashtags:"):
            result["hashtags"] = line.replace("Hashtags:", "").strip().split()
    return result
