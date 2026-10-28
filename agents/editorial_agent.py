"""
agents/editorial_agent.py — Editorial Review Agent
====================================================
Reviews blog drafts for readability, SEO, engagement, and factual accuracy.
Performs multi-level audience sentiment analysis on comments/feedback.
Implements the human-in-the-loop approval gate.

Capabilities:
  • review_draft(content, topic, llm)     — full AI editorial review
  • analyze_sentiment(text)               — single-text sentiment scoring
  • analyze_audience_comments(comments)  — aggregate comment sentiment
  • human_approval_check(review)         — approval gate logic
"""

import re
from config import Config


# ── Sentiment lexicons ─────────────────────────────────────────────────────────

_POS_WORDS = {
    "great", "excellent", "amazing", "love", "fantastic", "helpful",
    "brilliant", "insightful", "wonderful", "best", "awesome", "superb",
    "interesting", "good", "useful", "informative", "clear", "well",
    "perfect", "nice", "enjoy", "enjoyed", "inspiring", "innovative",
    "outstanding", "impressive", "engaging", "thorough", "accurate",
    "recommend", "valuable", "practical", "effective", "solid", "easy",
}

_NEG_WORDS = {
    "bad", "terrible", "awful", "boring", "confusing", "wrong", "poor",
    "worst", "useless", "unclear", "hate", "disappointed", "disappointing",
    "misleading", "inaccurate", "spam", "irrelevant", "weak", "shallow",
    "clickbait", "outdated", "biased", "complex", "difficult", "lacking",
    "incomplete", "vague", "repetitive", "waste", "mediocre",
}

_INTENSIFIERS = {"very", "extremely", "absolutely", "really", "totally", "quite"}

# ── Core sentiment analysis ────────────────────────────────────────────────────

def analyze_sentiment(text: str) -> dict:
    """
    Fast lexicon-based sentiment analysis (no ML dependencies required).
    Respects negation (not, never, isn't) and intensity modifiers.
    Returns score (-1.0 to +1.0), label, emoji, and word counts.
    """
    words = re.findall(r"\b\w+\b", text.lower())

    pos = 0
    neg = 0
    intensifier_active = False
    negate = False

    for i, word in enumerate(words):
        # Check for negation in prior word
        negate = (i > 0 and words[i - 1] in {"not", "never", "isn't", "wasn't", "no"})
        intensifier_active = (i > 0 and words[i - 1] in _INTENSIFIERS)

        weight = 1.5 if intensifier_active else 1.0
        if word in _POS_WORDS:
            if negate:
                neg += weight
            else:
                pos += weight
        elif word in _NEG_WORDS:
            if negate:
                pos += weight
            else:
                neg += weight

    total = (pos + neg) or 1
    score = round((pos - neg) / total, 3)

    if score > 0.25:
        label, emoji = "Positive", "😊"
    elif score < -0.25:
        label, emoji = "Negative", "😟"
    else:
        label, emoji = "Neutral", "😐"

    return {
        "score":      score,
        "label":      label,
        "emoji":      emoji,
        "pos_count":  int(pos),
        "neg_count":  int(neg),
        "word_count": len(words),
    }


def analyze_audience_comments(comments: list[str]) -> dict:
    """
    Aggregate sentiment across a list of audience comments.
    Returns overall stats, per-comment breakdown, and key themes.
    """
    if not comments:
        return {"overall": "No comments provided", "score": 0, "breakdown": []}

    results = [analyze_sentiment(c) for c in comments]
    avg_score  = round(sum(r["score"] for r in results) / len(results), 3)
    pos_count  = sum(1 for r in results if r["label"] == "Positive")
    neg_count  = sum(1 for r in results if r["label"] == "Negative")
    neu_count  = sum(1 for r in results if r["label"] == "Neutral")
    total      = len(comments)

    if avg_score > 0.2:
        overall_label = "Mostly Positive 😊"
    elif avg_score < -0.2:
        overall_label = "Mostly Negative 😟"
    elif pos_count > neg_count:
        overall_label = "Slightly Positive 🙂"
    elif neg_count > pos_count:
        overall_label = "Slightly Negative 🙁"
    else:
        overall_label = "Mixed / Neutral 😐"

    return {
        "overall":   overall_label,
        "avg_score": avg_score,
        "pos_count": pos_count,
        "neg_count": neg_count,
        "neu_count": neu_count,
        "total":     total,
        "breakdown": [
            {"comment": c[:140], **r}
            for c, r in zip(comments, results)
        ],
    }


# ── AI editorial review ────────────────────────────────────────────────────────

def review_draft(draft_content: str, topic: str, llm) -> dict:
    """
    Full AI editorial review using IBM Granite.
    Evaluates readability, SEO quality, engagement, and factual integrity.
    Returns structured feedback with scores, strengths, and improvement suggestions.
    """
    if not draft_content or len(draft_content) < 80:
        return {"error": "Draft is too short to review (minimum 80 characters)."}

    system = (
        "You are a senior editor, SEO expert, and fact-checker at a leading digital publication. "
        "Review blog drafts with rigour and constructiveness. "
        "Assess: readability for the intended audience, keyword usage and SEO structure, "
        "audience engagement hooks, factual accuracy, and overall editorial quality. "
        "Be specific — cite exact phrases or sections where needed. "
        "Do not rewrite the draft; only review it."
    )
    user_msg = (
        f"Review this blog draft about: '{topic}'\n\n"
        f"---\n{draft_content[:3500]}\n---\n\n"
        "Provide editorial feedback in this EXACT format "
        "(include all sections, even if brief):\n\n"
        "**Readability Score:** [1-10]\n"
        "**SEO Score:** [1-10]\n"
        "**Engagement Score:** [1-10]\n\n"
        "**Strengths:**\n"
        "- [specific strength 1]\n"
        "- [specific strength 2]\n"
        "- [specific strength 3]\n\n"
        "**Improvements Needed:**\n"
        "- [specific improvement 1]\n"
        "- [specific improvement 2]\n"
        "- [specific improvement 3]\n\n"
        "**Fact-Check Flags:**\n"
        "- [questionable claim or statistic, or write 'None identified']\n\n"
        "**SEO Recommendations:**\n"
        "- [specific SEO improvement]\n"
        "- [meta/keyword suggestion]\n\n"
        "**Overall Verdict:** [Approve / Needs Revision / Major Revision Required]"
    )

    try:
        raw = llm.ask(system, user_msg, max_tokens=Config.REVIEW_MAX_TOKENS, temperature=0.4)
    except Exception as exc:
        return {"error": f"Review failed: {exc}"}

    review: dict = {
        "readability":       0,
        "seo":               0,
        "engagement":        0,
        "strengths":         [],
        "improvements":      [],
        "fact_flags":        [],
        "seo_recommendations": [],
        "verdict":           "Needs Revision",
        "raw":               raw,
    }

    section: str | None = None
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("**Readability Score:**"):
            m = re.search(r"\d+", s)
            if m:
                review["readability"] = min(10, int(m.group()))
        elif s.startswith("**SEO Score:**"):
            m = re.search(r"\d+", s)
            if m:
                review["seo"] = min(10, int(m.group()))
        elif s.startswith("**Engagement Score:**"):
            m = re.search(r"\d+", s)
            if m:
                review["engagement"] = min(10, int(m.group()))
        elif "**Strengths:**" in s:
            section = "strengths"
        elif "**Improvements Needed:**" in s or "**Improvements:**" in s:
            section = "improvements"
        elif "**Fact-Check Flags:**" in s:
            section = "fact_flags"
        elif "**SEO Recommendations:**" in s:
            section = "seo_recommendations"
        elif s.startswith("**Overall Verdict:**"):
            review["verdict"] = s.replace("**Overall Verdict:**", "").strip()
            section = None
        elif s.startswith("- ") and section in (
            "strengths", "improvements", "fact_flags", "seo_recommendations"
        ):
            item = s[2:].strip()
            if item and item.lower() not in ("none", "none identified", "n/a"):
                review[section].append(item)

    return review


# ── Human-in-the-loop approval gate ───────────────────────────────────────────

def human_approval_check(review: dict) -> tuple[bool, str]:
    """
    Determine automatic approval recommendation based on editorial scores.
    Returns (approved: bool, message: str).

    Thresholds:
      • avg ≥ 7.5 AND 'Approve' verdict  → Auto-approve recommended
      • avg ≥ 5.5                         → Minor revision needed
      • avg < 5.5                         → Major revision required
    """
    if "error" in review:
        return False, f"⚠️ Review error: {review['error']}"

    r = review["readability"]
    s = review["seo"]
    e = review["engagement"]
    avg = round((r + s + e) / 3, 1)
    verdict = review.get("verdict", "")

    if avg >= 7.5 and "Approve" in verdict:
        return True, (
            f"✅ AI recommends approval (avg score: {avg}/10). "
            f"Readability {r}/10 · SEO {s}/10 · Engagement {e}/10"
        )
    elif avg >= 5.5:
        return False, (
            f"⚠️ Minor revision recommended before publishing "
            f"(avg score: {avg}/10). "
            "Address the improvement suggestions, then re-review."
        )
    else:
        return False, (
            f"❌ Major revision required (avg score: {avg}/10). "
            f"Readability {r}/10 · SEO {s}/10 · Engagement {e}/10. "
            "Please significantly rework the draft."
        )
