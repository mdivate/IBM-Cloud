"""
agents/content_agent.py — Content Generation Agent
====================================================
Generates SEO-optimised blog drafts using IBM Granite via watsonx.ai.
Accepts multi-modal inputs: text notes, image descriptions, voice transcripts.
Applies responsible AI guardrails before every LLM call.

Capabilities:
  • generate_blog_draft(...)       — full SEO blog post with structured output
  • generate_social_snippets(...)  — Twitter/X, LinkedIn, Instagram posts
  • process_voice_input(audio)     — voice-to-text transcription
  • guardrail_check(text)          — responsible AI content filter
"""

import re
from config import Config


# ── Responsible AI guardrails ──────────────────────────────────────────────────

def guardrail_check(text: str) -> tuple[bool, str]:
    """
    Input/output safety filter.
    Returns (is_safe: bool, reason: str).
    Blocks content matching any configured harmful keyword category.
    """
    lower = text.lower()
    for kw in Config.BLOCKED_KEYWORDS:
        if kw in lower:
            return False, (
                f"⛔ Content blocked by responsible AI guardrail: "
                f"detected '{kw}'. Please revise your input."
            )
    return True, ""


def _safe_generate(system: str, user_msg: str, llm, max_tokens: int, temperature: float) -> str:
    """
    Wrapper that checks both input and output for guardrail violations.
    Raises ValueError if either check fails.
    """
    # Input check
    combined_input = system + " " + user_msg
    safe, reason = guardrail_check(combined_input)
    if not safe:
        raise ValueError(reason)

    raw = llm.ask(system, user_msg, max_tokens=max_tokens, temperature=temperature)

    # Output check
    safe, reason = guardrail_check(raw)
    if not safe:
        raise ValueError(
            f"⛔ LLM output blocked by responsible AI guardrail: {reason}"
        )
    return raw


# ── Blog draft generation ──────────────────────────────────────────────────────

def generate_blog_draft(
    topic: str,
    research_summary: str,
    tone: str,
    word_count: int,
    extra_context: str,
    llm,
    include_citations: bool = True,
) -> dict:
    """
    Generate a full SEO-optimised blog draft using IBM Granite.

    Returns a structured dict with:
      seo_title, meta_description, content, suggested_tags,
      link_suggestions, focus_keyword, word_count_est, raw
    """
    # Guardrail input check
    safe, reason = guardrail_check(topic + " " + (extra_context or ""))
    if not safe:
        return {"error": reason}

    system = (
        "You are an expert blog writer, SEO specialist, and content strategist "
        "working for a top digital publication. "
        "Your blog posts are engaging, well-researched, SEO-optimised, and reader-friendly. "
        "Rules you always follow:\n"
        "• Use a compelling hook in the introduction\n"
        "• Include descriptive H2 and H3 subheadings\n"
        "• Naturally weave in the focus keyword 3-5 times\n"
        "• Cite research sources where provided\n"
        "• End with a clear call-to-action\n"
        "• Never plagiarise — all content must be original\n"
        "• Be factual; do not fabricate statistics or quotes\n"
        "• Avoid harmful, misleading, or biased content"
    )

    research_section = (
        f"\nResearch context (use this to add depth and cite sources):\n"
        f"{research_summary}\n"
        if research_summary.strip()
        else "\nNo research context provided — draw from general knowledge.\n"
    )
    extra_section = (
        f"\nAdditional author notes / context:\n{extra_context}\n"
        if extra_context and extra_context.strip()
        else ""
    )

    user_msg = (
        f"Write a {word_count}-word blog post on: **'{topic}'**\n\n"
        f"Tone: {tone}\n"
        f"{research_section}"
        f"{extra_section}\n"
        "Structure your response EXACTLY in this format:\n\n"
        "**SEO Title:** [compelling title, 50-65 chars]\n"
        "**Focus Keyword:** [primary SEO keyword phrase]\n"
        "**Meta Description:** [enticing description, 140-160 chars]\n\n"
        "**Blog Post:**\n"
        "[Full blog post — hook intro, 3-5 H2 sections with H3 subsections where needed, "
        "conclusion with CTA. Use Markdown formatting.]\n\n"
        "**Suggested Tags:** [tag1, tag2, tag3, tag4, tag5]\n"
        "**Link Suggestions:** [3 relevant internal or external link topics/URLs]\n"
        "**Estimated Word Count:** [number]"
    )

    try:
        raw = _safe_generate(system, user_msg, llm, Config.DRAFT_MAX_TOKENS, 0.75)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"LLM generation failed: {e}"}

    # ── Parse structured output ───────────────────────────────────────────────
    result: dict = {
        "seo_title":        "",
        "focus_keyword":    "",
        "meta_description": "",
        "content":          "",
        "suggested_tags":   [],
        "link_suggestions": [],
        "word_count_est":   0,
        "raw":              raw,
    }

    content_lines: list[str] = []
    section = None

    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("**SEO Title:**"):
            result["seo_title"] = s.replace("**SEO Title:**", "").strip()
            section = None
        elif s.startswith("**Focus Keyword:**"):
            result["focus_keyword"] = s.replace("**Focus Keyword:**", "").strip()
            section = None
        elif s.startswith("**Meta Description:**"):
            result["meta_description"] = s.replace("**Meta Description:**", "").strip()
            section = None
        elif s.startswith("**Blog Post:**"):
            section = "blog"
        elif s.startswith("**Suggested Tags:**"):
            section = None
            tags_raw = s.replace("**Suggested Tags:**", "").strip()
            result["suggested_tags"] = [
                t.strip().lstrip("#") for t in tags_raw.split(",") if t.strip()
            ]
        elif s.startswith("**Link Suggestions:**"):
            section = "links"
            link_raw = s.replace("**Link Suggestions:**", "").strip()
            if link_raw:
                result["link_suggestions"].append(link_raw)
        elif s.startswith("**Estimated Word Count:**"):
            m = re.search(r"\d+", s)
            if m:
                result["word_count_est"] = int(m.group())
            section = None
        elif section == "blog":
            content_lines.append(line)
        elif section == "links" and s and not s.startswith("**"):
            result["link_suggestions"].append(s)

    result["content"] = "\n".join(content_lines).strip()
    if not result["content"]:
        result["content"] = raw  # fallback

    return result


# ── Social media snippet generation ───────────────────────────────────────────

def generate_social_snippets(blog_title: str, blog_excerpt: str, llm) -> dict:
    """
    Generate platform-optimised social media posts for Twitter/X,
    LinkedIn, and Instagram to promote a published blog post.
    """
    system = (
        "You are a social media strategist and copywriter. "
        "Write platform-specific posts that maximise engagement and clicks. "
        "Twitter/X: punchy, max 280 chars, 2-3 hashtags. "
        "LinkedIn: professional, value-focused, 2-3 sentences. "
        "Instagram: engaging, emotive, 5-7 hashtags in caption."
    )
    user_msg = (
        f"Blog title: {blog_title}\n"
        f"Blog excerpt: {blog_excerpt[:450]}\n\n"
        "Write promotional posts for each platform. "
        "Format EXACTLY as:\n\n"
        "**Twitter/X:** [post text]\n"
        "**LinkedIn:** [post text]\n"
        "**Instagram:** [post text]\n"
    )
    try:
        raw = _safe_generate(system, user_msg, llm, Config.SOCIAL_MAX_TOKENS, 0.8)
    except ValueError as e:
        return {"twitter": str(e), "linkedin": "", "instagram": ""}
    except Exception as e:
        return {"twitter": f"Error: {e}", "linkedin": "", "instagram": ""}

    snippets: dict = {"twitter": "", "linkedin": "", "instagram": ""}
    current: str | None = None

    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("**Twitter/X:**") or s.startswith("**Twitter:**"):
            current = "twitter"
            content = re.sub(r"\*\*Twitter(/X|):\*\*", "", s).strip()
            snippets["twitter"] = content
        elif s.startswith("**LinkedIn:**"):
            current = "linkedin"
            content = s.replace("**LinkedIn:**", "").strip()
            snippets["linkedin"] = content
        elif s.startswith("**Instagram:**"):
            current = "instagram"
            content = s.replace("**Instagram:**", "").strip()
            snippets["instagram"] = content
        elif current and s and not s.startswith("**"):
            snippets[current] += (" " + s) if snippets[current] else s

    return snippets


# ── Voice input processing ─────────────────────────────────────────────────────

def process_voice_input(audio_file) -> str:
    """
    Transcribe an uploaded audio file using SpeechRecognition (Google STT).
    Gracefully degrades if audio libraries are not available.
    """
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except ImportError:
        return (
            "[Voice transcription unavailable — PyAudio not installed. "
            "Please type your input instead.]"
        )
    except Exception as exc:
        return f"[Voice transcription failed: {exc}. Please type your input.]"
