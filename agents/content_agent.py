"""
agents/content_agent.py
Generates SEO-friendly blog drafts from topic + research context.
Accepts text, image description, and voice transcript inputs.
"""

import re
from config import Config


def _guardrail_check(text: str) -> tuple[bool, str]:
    """Returns (is_safe, reason). Blocks content violating responsible AI rules."""
    lower = text.lower()
    for kw in Config.BLOCKED_KEYWORDS:
        if kw in lower:
            return False, f"Content blocked: contains '{kw}'. Please revise."
    return True, ""


def generate_blog_draft(
    topic: str,
    research_summary: str,
    tone: str,
    word_count: int,
    extra_context: str,
    llm,
) -> dict:
    """
    Generate a full SEO-optimised blog draft.
    Returns dict with title, meta_description, content, sources_used.
    """
    safe, reason = _guardrail_check(topic + " " + extra_context)
    if not safe:
        return {"error": reason}

    system = (
        "You are an expert blog writer, SEO specialist, and content strategist. "
        "Write engaging, well-structured, SEO-optimised blog posts. "
        "Always include: SEO title, meta description, H2 headings, "
        "a call-to-action, and internal/external link suggestions. "
        "Never plagiarise. Cite sources where provided. "
        "Be factual, original, and reader-friendly."
    )

    user_msg = (
        f"Write a {word_count}-word blog post on: '{topic}'\n\n"
        f"Tone: {tone}\n\n"
        f"Research context:\n{research_summary}\n\n"
        f"Additional context / notes from author:\n{extra_context or 'None'}\n\n"
        "Structure your response EXACTLY as:\n"
        "**SEO Title:** [title]\n"
        "**Meta Description:** [150 char max]\n"
        "**Blog Post:**\n"
        "[Full blog post with H2 headings, intro, body sections, conclusion, CTA]\n"
        "**Suggested Tags:** [comma-separated]\n"
        "**Link Suggestions:** [2-3 relevant URLs or topics to link]\n"
    )

    raw = llm.ask(system, user_msg, max_tokens=2000, temperature=0.75)

    # Parse structured output
    result = {
        "seo_title":        "",
        "meta_description": "",
        "content":          "",
        "suggested_tags":   [],
        "link_suggestions": [],
        "raw":              raw,
    }

    lines = raw.splitlines()
    content_started = False
    content_lines   = []
    after_content   = False

    for line in lines:
        if line.startswith("**SEO Title:**"):
            result["seo_title"] = line.replace("**SEO Title:**", "").strip()
        elif line.startswith("**Meta Description:**"):
            result["meta_description"] = line.replace("**Meta Description:**", "").strip()
        elif line.startswith("**Blog Post:**"):
            content_started = True
            after_content   = False
        elif line.startswith("**Suggested Tags:**"):
            content_started = False
            after_content   = True
            tags = line.replace("**Suggested Tags:**", "").strip()
            result["suggested_tags"] = [t.strip() for t in tags.split(",") if t.strip()]
        elif line.startswith("**Link Suggestions:**"):
            result["link_suggestions"] = [line.replace("**Link Suggestions:**", "").strip()]
        elif content_started and not after_content:
            content_lines.append(line)

    result["content"] = "\n".join(content_lines).strip()
    if not result["content"]:
        result["content"] = raw  # fallback: show raw if parsing fails

    return result


def generate_social_snippets(blog_title: str, blog_excerpt: str, llm) -> dict:
    """Generate Twitter/X, LinkedIn, and Instagram captions for the blog post."""
    system = (
        "You are a social media marketing expert. "
        "Write platform-optimised social media posts to promote a blog article."
    )
    user_msg = (
        f"Blog title: {blog_title}\n"
        f"Blog excerpt: {blog_excerpt[:400]}\n\n"
        "Write promotional posts for:\n"
        "**Twitter/X:** [max 280 chars, include 3 hashtags]\n"
        "**LinkedIn:** [professional tone, 2-3 sentences]\n"
        "**Instagram:** [engaging caption + 5 hashtags]\n"
    )
    raw = llm.ask(system, user_msg, max_tokens=400, temperature=0.8)

    snippets = {"twitter": "", "linkedin": "", "instagram": ""}
    current = None
    for line in raw.splitlines():
        if "**Twitter/X:**" in line or "**Twitter:**" in line:
            current = "twitter"
            snippets["twitter"] = line.split(":", 2)[-1].strip()
        elif "**LinkedIn:**" in line:
            current = "linkedin"
            snippets["linkedin"] = line.split(":", 2)[-1].strip()
        elif "**Instagram:**" in line:
            current = "instagram"
            snippets["instagram"] = line.split(":", 2)[-1].strip()
        elif current and line.strip():
            snippets[current] += " " + line.strip()

    return snippets


def process_voice_input(audio_file) -> str:
    """
    Transcribe an uploaded audio file using SpeechRecognition.
    Falls back gracefully if audio libs are unavailable.
    """
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except ImportError:
        return "[Voice transcription requires PyAudio. Please type your input instead.]"
    except Exception as e:
        return f"[Transcription failed: {e}. Please type your input.]"
