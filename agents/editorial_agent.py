"""
agents/editorial_agent.py
Reviews blog drafts for quality, SEO, readability, and tone.
Performs audience sentiment analysis on comments/feedback.
"""

import re
from config import Config


# ── Simple sentiment without heavy ML deps ────────────────────────────────────

_POS_WORDS = {
    "great","excellent","amazing","love","fantastic","helpful","brilliant",
    "insightful","wonderful","best","awesome","superb","interesting","good",
    "useful","informative","clear","well","perfect","nice","enjoy","enjoyed",
}
_NEG_WORDS = {
    "bad","terrible","awful","boring","confusing","wrong","poor","worst",
    "useless","unclear","hate","disappointed","disappointing","misleading",
    "inaccurate","spam","irrelevant","weak","shallow","clickbait",
}


def analyze_sentiment(text: str) -> dict:
    """
    Fast lexicon-based sentiment analysis (no ML deps required).
    Returns score (-1 to +1), label, and pos/neg word counts.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    pos = sum(1 for w in words if w in _POS_WORDS)
    neg = sum(1 for w in words if w in _NEG_WORDS)
    total = pos + neg or 1
    score = round((pos - neg) / total, 3)

    if score > 0.2:
        label = "Positive"
        emoji = "😊"
    elif score < -0.2:
        label = "Negative"
        emoji = "😟"
    else:
        label = "Neutral"
        emoji = "😐"

    return {
        "score":      score,
        "label":      label,
        "emoji":      emoji,
        "pos_count":  pos,
        "neg_count":  neg,
        "word_count": len(words),
    }


def analyze_audience_comments(comments: list[str]) -> dict:
    """
    Aggregate sentiment across a list of audience comments.
    Returns overall stats and per-comment breakdown.
    """
    if not comments:
        return {"overall": "No comments", "score": 0, "breakdown": []}

    results = [analyze_sentiment(c) for c in comments]
    avg_score = round(sum(r["score"] for r in results) / len(results), 3)
    pos_count = sum(1 for r in results if r["label"] == "Positive")
    neg_count = sum(1 for r in results if r["label"] == "Negative")
    neu_count = sum(1 for r in results if r["label"] == "Neutral")

    if avg_score > 0.15:
        overall_label = "Mostly Positive 😊"
    elif avg_score < -0.15:
        overall_label = "Mostly Negative 😟"
    else:
        overall_label = "Mixed / Neutral 😐"

    return {
        "overall":       overall_label,
        "avg_score":     avg_score,
        "pos_count":     pos_count,
        "neg_count":     neg_count,
        "neu_count":     neu_count,
        "total":         len(comments),
        "breakdown":     [
            {"comment": c[:120], **r} for c, r in zip(comments, results)
        ],
    }


def review_draft(draft_content: str, topic: str, llm) -> dict:
    """
    Editorial AI review: readability, SEO score, improvements, fact-check flags.
    Returns structured feedback dict.
    """
    if not draft_content or len(draft_content) < 100:
        return {"error": "Draft too short to review."}

    system = (
        "You are a senior editor, SEO expert, and fact-checker at a major publication. "
        "Review blog drafts for quality, accuracy, readability, and SEO. "
        "Be constructive and specific. Do not rewrite the entire post — only review it."
    )
    user_msg = (
        f"Review this blog draft about '{topic}':\n\n"
        f"{draft_content[:3000]}\n\n"
        "Provide feedback in this EXACT format:\n"
        "**Readability Score:** [1-10]\n"
        "**SEO Score:** [1-10]\n"
        "**Engagement Score:** [1-10]\n"
        "**Strengths:**\n- [point 1]\n- [point 2]\n"
        "**Improvements:**\n- [point 1]\n- [point 2]\n- [point 3]\n"
        "**Fact-Check Flags:**\n- [any questionable claims or 'None']\n"
        "**Overall Verdict:** [Approve / Needs Revision / Major Revision]"
    )
    raw = llm.ask(system, user_msg, max_tokens=600, temperature=0.4)

    review = {
        "readability":  0,
        "seo":          0,
        "engagement":   0,
        "strengths":    [],
        "improvements": [],
        "fact_flags":   [],
        "verdict":      "Needs Revision",
        "raw":          raw,
    }

    section = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("**Readability Score:**"):
            try:
                review["readability"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line.startswith("**SEO Score:**"):
            try:
                review["seo"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif line.startswith("**Engagement Score:**"):
            try:
                review["engagement"] = int(re.search(r"\d+", line).group())
            except Exception:
                pass
        elif "**Strengths:**" in line:
            section = "strengths"
        elif "**Improvements:**" in line:
            section = "improvements"
        elif "**Fact-Check Flags:**" in line:
            section = "fact_flags"
        elif line.startswith("**Overall Verdict:**"):
            review["verdict"] = line.replace("**Overall Verdict:**", "").strip()
            section = None
        elif line.startswith("- ") and section in ("strengths", "improvements", "fact_flags"):
            review[section].append(line[2:].strip())

    return review


def human_approval_check(review: dict) -> tuple[bool, str]:
    """
    Simple human-in-the-loop gate based on editorial scores.
    Returns (approved, message).
    """
    if "error" in review:
        return False, review["error"]

    avg = (review["readability"] + review["seo"] + review["engagement"]) / 3
    verdict = review.get("verdict", "")

    if avg >= 7 and "Approve" in verdict:
        return True, f"✅ Draft approved (avg score: {avg:.1f}/10)"
    elif avg >= 5:
        return False, (
            f"⚠️ Needs revision before publishing (avg score: {avg:.1f}/10). "
            "Address the improvement suggestions and resubmit."
        )
    else:
        return False, (
            f"❌ Major revision required (avg score: {avg:.1f}/10). "
            "Please significantly rework the draft."
        )
