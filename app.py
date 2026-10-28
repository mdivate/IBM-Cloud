"""
app.py — Writing Pulse: Agentic AI Blogging Assistant
=======================================================
Streamlit dashboard powered by IBM watsonx.ai + IBM Granite LLM.

Pages:
  📊 Dashboard       — Live headlines, trending keywords, system status
  🔍 Research        — RSS-based research with AI synthesis and citations
  📈 Trends          — Keyword trends, AI blog topic suggestions
  ✏️  Write Blog      — Multi-modal SEO blog draft generation
  🎯 Editorial       — AI review scores + human approval gate
  💬 Audience        — Sentiment analysis on comments/feedback
  📱 Social Media    — Platform-specific post generation + engagement
  ⚙️  Settings        — Config viewer, guardrails, RSS feeds

Run with:
    streamlit run app.py
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from PIL import Image

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from watsonx_client import llm
from agents.research_agent  import (
    fetch_rss_articles, fetch_top_headlines,
    summarize_research, format_citations,
)
from agents.trend_agent import (
    get_trending_topics, suggest_blog_topics,
    predict_engagement, get_topic_heatmap,
)
from agents.content_agent import (
    generate_blog_draft, generate_social_snippets,
    process_voice_input, guardrail_check,
)
from agents.editorial_agent import (
    review_draft, analyze_audience_comments,
    human_approval_check, analyze_sentiment,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Writing Pulse — AI Blogging Assistant",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Header */
  .main-header {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 55%, #1a56db 100%);
    padding: 1.6rem 2rem; border-radius: 14px; margin-bottom: 1.4rem; color: white;
  }
  .main-header h1 { font-size: 2.1rem; margin: 0; font-weight: 700; }
  .main-header p  { margin: 0.4rem 0 0; opacity: 0.85; font-size: 0.95rem; }

  /* Metric / info cards */
  .metric-card {
    background: #f7f9fc; border: 1px solid #dde3ed;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem;
    line-height: 1.5;
  }
  .metric-card-green  { border-left: 4px solid #24a148; }
  .metric-card-orange { border-left: 4px solid #f1620a; }
  .metric-card-blue   { border-left: 4px solid #0f62fe; }

  /* Topic chips */
  .topic-chip {
    display: inline-block; background: #e8f1ff; color: #0f62fe;
    border: 1px solid #c0d4f5; border-radius: 16px;
    padding: 3px 12px; font-size: 0.8rem; margin: 3px; font-weight: 500;
  }

  /* Section labels */
  .section-label {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; color: #525252; margin-bottom: 4px;
  }

  /* Verdict / status badges */
  .badge-green  { background:#d4f1d4; color:#155724; padding:3px 10px; border-radius:12px; font-size:0.82rem; font-weight:600; }
  .badge-orange { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:12px; font-size:0.82rem; font-weight:600; }
  .badge-red    { background:#fde8e8; color:#b91c1c; padding:3px 10px; border-radius:12px; font-size:0.82rem; font-weight:600; }

  /* IBM / model badge */
  .ibm-badge {
    display: inline-block; background: #0f62fe; color: white;
    border-radius: 20px; padding: 3px 12px; font-size: 0.73rem;
    font-weight: 700; letter-spacing: 0.3px;
  }
  .granite-badge {
    display: inline-block; background: #6929c4; color: white;
    border-radius: 20px; padding: 3px 12px; font-size: 0.73rem;
    font-weight: 700; letter-spacing: 0.3px; margin-left: 6px;
  }

  /* Footer */
  .footer {
    text-align: center; padding: 1.5rem; color: #8d8d8d;
    font-size: 0.75rem; border-top: 1px solid #e5e7eb; margin-top: 2.5rem;
  }

  /* Citation block */
  .citation-box {
    background: #f0f4ff; border-left: 3px solid #0f62fe;
    padding: 0.7rem 1rem; border-radius: 0 8px 8px 0;
    font-size: 0.83rem; margin-top: 0.5rem;
  }

  /* Step guide */
  .step-card {
    background: white; border: 1px solid #dde3ed; border-radius: 10px;
    padding: 1rem; text-align: center;
  }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "research_articles":  [],
        "research_summary":   "",
        "research_citations": "",
        "trending_topics":    [],
        "topic_suggestions":  [],
        "blog_draft":         {},
        "review_result":      {},
        "engagement_pred":    {},
        "social_snippets":    {},
        "sentiment_result":   {},
        "approval_status":    None,
        "current_topic":      "",
        "_headlines":         [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Shared helpers ────────────────────────────────────────────────────────────

def _check_api_key() -> bool:
    if not Config.WATSONX_API_KEY:
        st.error(
            "⚠️ **WATSONX_API_KEY not configured.** "
            "Add your IBM Cloud API key to `.env` and restart Streamlit."
        )
        return False
    return True


def _score_gauge(score: int, title: str, out_of: int = 10):
    color = "#24a148" if score >= 7 else "#f1620a" if score >= 5 else "#da1e28"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, out_of]},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,    out_of*0.4], "color": "#fde8e8"},
                {"range": [out_of*0.4, out_of*0.7], "color": "#fff3cd"},
                {"range": [out_of*0.7, out_of],     "color": "#d4edda"},
            ],
        },
    ))
    fig.update_layout(height=185, margin=dict(t=35, b=10, l=10, r=10))
    return fig


def _sentiment_donut(pos: int, neg: int, neu: int):
    fig = px.pie(
        values=[pos, neg, neu],
        names=["Positive", "Negative", "Neutral"],
        color_discrete_sequence=["#24a148", "#da1e28", "#8d8d8d"],
        hole=0.56,
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(
        height=250, margin=dict(t=15, b=15, l=15, r=15),
        showlegend=True, legend=dict(orientation="h", y=-0.1),
    )
    return fig


def _engagement_bar(score: int):
    color = "#24a148" if score >= 70 else "#f1620a" if score >= 45 else "#da1e28"
    fig = go.Figure(go.Bar(
        x=[score], y=["Engagement Score"], orientation="h",
        marker_color=color,
        text=[f"{score}/100"], textposition="inside",
        textfont={"color": "white", "size": 14},
    ))
    fig.update_layout(
        height=100, margin=dict(t=5, b=5, l=5, r=5),
        xaxis=dict(range=[0, 100], showgrid=False, showticklabels=False),
        yaxis=dict(showticklabels=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _trend_bar(trending: list[dict]):
    df = pd.DataFrame(trending[:12])
    fig = px.bar(
        df, x="count", y="keyword", orientation="h",
        color="count",
        color_continuous_scale=["#c0d4f5", "#0f62fe", "#0a3ea0"],
        title="Keyword Frequency Across Live News Feeds",
    )
    fig.update_layout(
        height=380, margin=dict(t=40, b=10, l=10, r=10),
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        xaxis_title="Mentions",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✍️ Writing Pulse")
    st.markdown(
        '<span class="ibm-badge">IBM watsonx.ai</span>'
        '<span class="granite-badge">Granite LLM</span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio(
        "Go to",
        [
            "📊 Dashboard",
            "🔍 Research",
            "📈 Trends",
            "✏️ Write Blog",
            "🎯 Editorial Review",
            "💬 Audience Insights",
            "📱 Social Media",
            "⚙️ Settings",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    api_status  = "🟢 API key set" if Config.WATSONX_API_KEY else "🔴 No API key"
    model_label = llm.active_model if Config.WATSONX_API_KEY else Config.WATSONX_MODEL_ID
    st.markdown(
        f"**Model:** `{model_label}`\n\n"
        f"**Endpoint:** `au-syd`\n\n"
        f"**Status:** {api_status}"
    )
    st.markdown("---")
    st.caption(f"© {datetime.now().year} Writing Pulse AI · v{Config.APP_VERSION}")


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    '<h1>✍️ Writing Pulse</h1>'
    f'<p>{Config.APP_TAGLINE}</p>'
    '</div>',
    unsafe_allow_html=True,
)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.subheader("📊 Writing Pulse Dashboard")

    # ── KPI metrics ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔥 Trending Topics",  len(st.session_state.trending_topics) or "—")
    c2.metric("📰 Articles Found",   len(st.session_state.research_articles) or "—")
    c3.metric("📝 Draft Status",
              "Ready ✅" if st.session_state.blog_draft.get("content") else "Not Started")
    c4.metric("🎯 Review Score",
              f"{round((st.session_state.review_result.get('readability',0)+st.session_state.review_result.get('seo',0)+st.session_state.review_result.get('engagement',0))/3,1)}/10"
              if st.session_state.review_result else "—")
    c5.metric("✅ Approval",         st.session_state.approval_status or "Pending")

    st.markdown("---")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("### 🗞️ Latest Headlines")
        if st.button("🔄 Fetch Live Headlines", use_container_width=True):
            with st.spinner("Fetching latest news from 10 feeds…"):
                st.session_state["_headlines"] = fetch_top_headlines(max_articles=10)

        for h in st.session_state.get("_headlines", []):
            st.markdown(
                f'<div class="metric-card metric-card-blue">'
                f'<b>{h["title"]}</b><br>'
                f'<small>📰 {h["source"]} &nbsp;·&nbsp; '
                f'<a href="{h["url"]}" target="_blank">Read →</a>'
                f'</small></div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("### 📈 Trending Keywords")
        if st.button("🔄 Refresh Trends", use_container_width=True):
            with st.spinner("Scanning 8 news feeds for trending keywords…"):
                st.session_state.trending_topics = get_trending_topics()

        if st.session_state.trending_topics:
            st.plotly_chart(
                _trend_bar(st.session_state.trending_topics),
                use_container_width=True,
            )
        else:
            st.info("Click **Refresh Trends** to load live keyword trends.")

    st.markdown("---")

    # ── Quick-start workflow guide ────────────────────────────────────────────
    st.markdown("### 🚀 Quick-Start Workflow")
    s1, s2, s3, s4 = st.columns(4)
    for col, icon, step, desc in [
        (s1, "1️⃣", "Research & Trends",   "Fetch live articles and trending keywords from 10 news sources"),
        (s2, "2️⃣", "Write Blog",          "Generate an SEO blog draft using IBM Granite LLM"),
        (s3, "3️⃣", "Editorial Review",    "AI scores + fact-check flags + human approval gate"),
        (s4, "4️⃣", "Social & Publish",    "Auto-generate social posts and predict engagement window"),
    ]:
        col.markdown(
            f'<div class="step-card">{icon}<br><b>{step}</b><br>'
            f'<small style="color:#525252">{desc}</small></div>',
            unsafe_allow_html=True,
        )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Research
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Research":
    st.subheader("🔍 Research Agent")
    st.caption(
        "Fetches real-time articles from 10 RSS feeds and uses "
        "IBM Granite to synthesize cited research summaries."
    )

    topic = st.text_input(
        "Research topic:",
        value=st.session_state.current_topic,
        placeholder="e.g. Generative AI in Healthcare",
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    fetch_btn     = col1.button("🔍 Fetch Articles",   use_container_width=True)
    summarize_btn = col2.button(
        "🧠 AI Synthesize",
        use_container_width=True,
        disabled=not bool(st.session_state.research_articles),
    )

    if fetch_btn:
        if not topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner(f"Searching 10 RSS feeds for '{topic}'…"):
                articles = fetch_rss_articles(topic)
                st.session_state.research_articles  = articles
                st.session_state.current_topic      = topic
                st.session_state.research_summary   = ""
                st.session_state.research_citations = ""
            st.success(f"✅ Found **{len(articles)}** relevant articles.")

    if summarize_btn:
        if not _check_api_key():
            st.stop()
        with st.spinner("IBM Granite is synthesising the research…"):
            summary   = summarize_research(
                st.session_state.research_articles,
                st.session_state.current_topic,
                llm,
            )
            citations = format_citations(st.session_state.research_articles)
            st.session_state.research_summary   = summary
            st.session_state.research_citations = citations

    # Articles list
    if st.session_state.research_articles:
        st.markdown(
            f"**{len(st.session_state.research_articles)} articles found for:** "
            f"`{st.session_state.current_topic}`"
        )
        for i, art in enumerate(st.session_state.research_articles[:12]):
            with st.expander(f"[{i+1}] {art['title']} — {art['source']}"):
                st.write(art["summary"])
                st.markdown(f"[🔗 Read full article]({art['url']})")
                st.caption(f"Published: {art['published']}")

    # AI summary
    if st.session_state.research_summary:
        st.markdown("---")
        st.markdown("### 🧠 AI Research Summary (IBM Granite)")
        st.markdown(
            f'<div class="metric-card metric-card-blue">'
            f'{st.session_state.research_summary}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.research_citations:
            with st.expander("📚 View Source Citations"):
                st.markdown(
                    f'<div class="citation-box">'
                    f'{st.session_state.research_citations}'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Trends
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📈 Trends":
    st.subheader("📈 Trend Analysis Agent")
    st.caption("Real-time keyword trends from 8 RSS feeds + IBM Granite topic suggestions.")

    col1, col2 = st.columns([1, 2])
    refresh_btn = col1.button("🔄 Refresh Trends", use_container_width=True)
    suggest_btn = col2.button(
        "💡 Suggest Blog Topics (IBM Granite)",
        use_container_width=True,
        disabled=not bool(st.session_state.trending_topics),
    )

    if refresh_btn:
        with st.spinner("Scanning news feeds…"):
            st.session_state.trending_topics  = get_trending_topics()
            st.session_state.topic_suggestions = []

    if suggest_btn:
        if not _check_api_key():
            st.stop()
        with st.spinner("IBM Granite is generating blog topic ideas…"):
            st.session_state.topic_suggestions = suggest_blog_topics(
                st.session_state.trending_topics, llm
            )

    if st.session_state.trending_topics:
        # Keyword chips
        st.markdown("#### 🔥 Trending Keywords")
        chips_html = " ".join(
            f'<span class="topic-chip">#{t["keyword"]} ({t["count"]})</span>'
            for t in st.session_state.trending_topics
        )
        st.markdown(chips_html, unsafe_allow_html=True)

        # Trend chart
        st.plotly_chart(
            _trend_bar(st.session_state.trending_topics),
            use_container_width=True,
        )

        # Supporting headlines
        st.markdown("#### 📋 Supporting Headlines by Keyword")
        for t in st.session_state.trending_topics[:6]:
            with st.expander(
                f"#{t['keyword']} — {t['count']} mentions "
                f"(sources: {', '.join(t.get('feed_sources', [])[:3])})"
            ):
                for h in t["headlines"]:
                    st.write(f"• {h}")

    if st.session_state.topic_suggestions:
        st.markdown("---")
        st.markdown("#### 💡 IBM Granite Blog Topic Suggestions")
        for i, s in enumerate(st.session_state.topic_suggestions):
            with st.expander(f"💡 {s.get('title', f'Topic {i+1}')}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Description:** {s.get('description', '')}")
                    st.write(f"**Audience:** {s.get('audience', '')}")
                    if s.get("angle"):
                        st.write(f"**Differentiating Angle:** {s.get('angle', '')}")
                    tags_html = " ".join(
                        f'<span class="topic-chip">{t}</span>'
                        for t in s.get("hashtags", [])
                    )
                    if tags_html:
                        st.markdown(tags_html, unsafe_allow_html=True)
                with c2:
                    if st.button(f"Use this topic →", key=f"use_topic_{i}"):
                        st.session_state.current_topic = s.get("title", "")
                        st.success(f"✅ Topic set! Go to **✏️ Write Blog**.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Write Blog
# ═════════════════════════════════════════════════════════════════════════════
elif page == "✏️ Write Blog":
    st.subheader("✏️ Content Generation Agent")
    st.caption("Generate SEO-optimised blog drafts with IBM Granite. Accepts text, image, and voice inputs.")

    if not _check_api_key():
        st.stop()

    with st.form("blog_form"):
        st.markdown("#### 📝 Blog Configuration")
        col1, col2 = st.columns(2)

        topic = col1.text_input(
            "Blog Topic *",
            value=st.session_state.current_topic,
            placeholder="e.g. How IBM Granite is Transforming Enterprise AI in 2025",
        )
        tone = col2.selectbox(
            "Writing Tone",
            ["Professional", "Conversational", "Educational", "Persuasive",
             "Storytelling", "Technical", "Inspirational", "Analytical"],
        )
        word_count = col1.slider("Target Word Count", 300, 2500, 900, 100)

        st.markdown("#### 🔍 Research Context")
        research_ctx = st.text_area(
            "Research summary (auto-filled if you ran Research):",
            value=st.session_state.research_summary,
            height=110,
            placeholder="Paste your research notes, data points, or context here…",
        )

        st.markdown("#### 📎 Additional Inputs")
        t1, t2, t3 = st.tabs(["📝 Text Notes", "🖼️ Image Context", "🎤 Voice Input"])

        with t1:
            extra_text = st.text_area(
                "Author notes / additional instructions:",
                height=80,
                placeholder="Any special instructions, personal insights, or data to include…",
            )

        with t2:
            uploaded_img = st.file_uploader(
                "Upload an image (PNG/JPG):", type=["png", "jpg", "jpeg"]
            )
            img_desc = ""
            if uploaded_img:
                img = Image.open(uploaded_img)
                st.image(img, caption="Uploaded image preview", width=320)
                img_desc = st.text_input(
                    "Describe this image for AI context:",
                    placeholder="e.g. A bar chart showing AI adoption rates 2020–2025 across industries",
                )

        with t3:
            audio_file = st.file_uploader("Upload a voice note (.wav):", type=["wav"])
            voice_text = ""
            if audio_file:
                voice_text = process_voice_input(audio_file)
                st.info(f"🎤 Transcribed: {voice_text}")

        extra_context = "\n".join(filter(None, [extra_text, img_desc, voice_text]))

        generate_btn = st.form_submit_button(
            "🚀 Generate Blog Draft with IBM Granite",
            use_container_width=True,
        )

    if generate_btn:
        if not topic.strip():
            st.error("Please enter a blog topic.")
        else:
            # Pre-check guardrails
            safe, reason = guardrail_check(topic + " " + extra_context)
            if not safe:
                st.error(reason)
                st.stop()

            with st.spinner("IBM Granite is writing your blog draft…"):
                draft = generate_blog_draft(
                    topic=topic,
                    research_summary=research_ctx,
                    tone=tone,
                    word_count=word_count,
                    extra_context=extra_context,
                    llm=llm,
                )
                st.session_state.blog_draft    = draft
                st.session_state.current_topic = topic

    # ── Draft display ─────────────────────────────────────────────────────────
    if st.session_state.blog_draft:
        draft = st.session_state.blog_draft

        if "error" in draft:
            st.error(draft["error"])
        else:
            st.markdown("---")
            st.markdown("### 📄 Generated Blog Draft")

            # Meta block
            meta_col, engage_col = st.columns([3, 2])
            with meta_col:
                if draft.get("seo_title"):
                    st.markdown(f"**🏷️ SEO Title:** {draft['seo_title']}")
                if draft.get("focus_keyword"):
                    st.markdown(f"**🔑 Focus Keyword:** `{draft['focus_keyword']}`")
                if draft.get("meta_description"):
                    st.markdown(f"**📋 Meta Description:** {draft['meta_description']}")
                if draft.get("word_count_est"):
                    st.markdown(f"**📊 Estimated Word Count:** ~{draft['word_count_est']}")
                tags_html = " ".join(
                    f'<span class="topic-chip">{t}</span>'
                    for t in draft.get("suggested_tags", [])
                )
                if tags_html:
                    st.markdown(f"**🏷️ Tags:**")
                    st.markdown(tags_html, unsafe_allow_html=True)

            with engage_col:
                if st.button("📊 Predict Engagement", use_container_width=True):
                    if _check_api_key():
                        with st.spinner("Predicting engagement…"):
                            st.session_state.engagement_pred = predict_engagement(
                                draft.get("seo_title") or st.session_state.current_topic, llm
                            )
                if st.session_state.engagement_pred:
                    ep = st.session_state.engagement_pred
                    st.plotly_chart(
                        _engagement_bar(ep.get("score", 70)),
                        use_container_width=True,
                    )
                    st.markdown(
                        f"📅 **{ep.get('best_day')}** @ **{ep.get('best_time')}**  \n"
                        f"📡 Reach: **{ep.get('reach', 'Medium')}**  \n"
                        f"📝 Type: *{ep.get('content_type', '—')}*  \n\n"
                        f"💬 {ep.get('reason', '')}"
                    )
                    if ep.get("hashtags"):
                        htags = " ".join(ep["hashtags"])
                        st.markdown(f"**#️⃣ Hashtags:** {htags}")

            st.markdown("---")
            st.markdown("#### 📝 Blog Content")
            content = draft.get("content") or draft.get("raw", "")
            st.markdown(content)

            # Research citations
            if st.session_state.research_citations:
                st.markdown(st.session_state.research_citations)

            # Link suggestions
            if draft.get("link_suggestions"):
                st.markdown("**🔗 Link Suggestions:**")
                for ls in draft["link_suggestions"]:
                    if ls.strip():
                        st.write(f"• {ls}")

            st.markdown("---")
            st.download_button(
                "⬇️ Download as Markdown",
                data=(
                    f"# {draft.get('seo_title', st.session_state.current_topic)}\n\n"
                    f"**Meta Description:** {draft.get('meta_description', '')}\n\n"
                    f"**Focus Keyword:** {draft.get('focus_keyword', '')}\n\n"
                    f"---\n\n{content}\n\n"
                    f"{st.session_state.research_citations}"
                ),
                file_name="blog_draft.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Editorial Review
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Editorial Review":
    st.subheader("🎯 Editorial Review Agent")
    st.caption(
        "AI-powered editorial review with readability, SEO, and engagement scoring. "
        "Human approval gate before publishing."
    )

    if not _check_api_key():
        st.stop()

    if not st.session_state.blog_draft.get("content"):
        st.info("📝 No draft yet. Go to **✏️ Write Blog** first.")
        st.stop()

    draft_content = (
        st.session_state.blog_draft.get("content")
        or st.session_state.blog_draft.get("raw", "")
    )
    topic = st.session_state.current_topic or "Blog Post"

    col1, col2 = st.columns([3, 1])
    col1.markdown(f"**Reviewing draft:** `{topic}`")
    review_btn = col2.button("🎯 Run AI Review", use_container_width=True)

    if review_btn:
        with st.spinner("IBM Granite editorial agent is reviewing your draft…"):
            review   = review_draft(draft_content, topic, llm)
            approved, msg = human_approval_check(review)
            st.session_state.review_result  = review
            st.session_state.approval_status = "Approved ✅" if approved else "Needs Revision ⚠️"

    if st.session_state.review_result:
        review = st.session_state.review_result

        if "error" in review:
            st.error(review["error"])
        else:
            # Score gauges
            st.markdown("### 📊 Quality Scores")
            g1, g2, g3 = st.columns(3)
            g1.plotly_chart(_score_gauge(review["readability"], "Readability"), use_container_width=True)
            g2.plotly_chart(_score_gauge(review["seo"],         "SEO Quality"), use_container_width=True)
            g3.plotly_chart(_score_gauge(review["engagement"],  "Engagement"),  use_container_width=True)

            avg = round((review["readability"] + review["seo"] + review["engagement"]) / 3, 1)
            st.markdown(f"**Average Score:** {avg}/10")

            # Verdict
            approved, approval_msg = human_approval_check(review)
            st.markdown("---")
            verdict = review.get("verdict", "Needs Revision")
            if approved:
                st.success(f"**Verdict:** {verdict}  |  {approval_msg}")
            else:
                st.warning(f"**Verdict:** {verdict}  |  {approval_msg}")

            # Detailed feedback
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ✅ Strengths")
                for s in review.get("strengths", []):
                    st.write(f"• {s}")
                if review.get("seo_recommendations"):
                    st.markdown("#### 🔍 SEO Recommendations")
                    for r in review["seo_recommendations"]:
                        st.write(f"• {r}")
            with c2:
                st.markdown("#### 🔧 Improvements Needed")
                for imp in review.get("improvements", []):
                    st.write(f"• {imp}")

            if review.get("fact_flags"):
                st.markdown("#### ⚠️ Fact-Check Flags")
                for flag in review["fact_flags"]:
                    st.warning(f"⚠️ {flag}")

            # Human approval gate
            st.markdown("---")
            st.markdown("### 🧑 Human Approval Gate")
            st.info(
                "**Responsible AI**: Review the AI feedback above, then make "
                "the final publishing decision. The AI recommends but humans decide."
            )
            hc1, hc2 = st.columns(2)
            if hc1.button("✅ Approve for Publishing", use_container_width=True, type="primary"):
                st.session_state.approval_status = "Approved ✅"
                st.success("✅ Draft **approved** for publishing!")
                st.balloons()
            if hc2.button("❌ Send Back for Revision", use_container_width=True):
                st.session_state.approval_status = "Needs Revision ⚠️"
                st.warning("Draft sent back for revision. Update the blog and re-review.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Audience Insights
# ═════════════════════════════════════════════════════════════════════════════
elif page == "💬 Audience Insights":
    st.subheader("💬 Audience Sentiment Analysis")
    st.caption(
        "Paste comments, social media replies, or survey responses. "
        "Multi-level lexicon-based sentiment analysis with negation handling."
    )

    comments_input = st.text_area(
        "Comments / feedback (one per line):",
        height=200,
        placeholder=(
            "Great article! Very helpful.\n"
            "Too long and boring.\n"
            "This completely changed my perspective.\n"
            "Not really accurate about the statistics.\n"
            "Absolutely love the examples given!"
        ),
    )

    analyze_btn = st.button("📊 Analyze Sentiment", use_container_width=False)
    if analyze_btn:
        comments = [c.strip() for c in comments_input.splitlines() if c.strip()]
        if not comments:
            st.warning("Please enter at least one comment.")
        else:
            with st.spinner("Analyzing sentiment…"):
                result = analyze_audience_comments(comments)
                st.session_state.sentiment_result = result

    if st.session_state.sentiment_result:
        r = st.session_state.sentiment_result
        st.markdown("---")
        st.markdown(f"### Overall Sentiment: {r['overall']}")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Comments",  r["total"])
        m2.metric("😊 Positive",     r["pos_count"])
        m3.metric("😟 Negative",     r["neg_count"])
        m4.metric("😐 Neutral",      r["neu_count"])
        m5.metric("📊 Avg Score",    f"{r['avg_score']:+.3f}")

        donut_col, table_col = st.columns([1, 2])
        with donut_col:
            st.plotly_chart(
                _sentiment_donut(r["pos_count"], r["neg_count"], r["neu_count"]),
                use_container_width=True,
            )

        with table_col:
            st.markdown("#### Per-Comment Breakdown")
            for item in r.get("breakdown", []):
                color = (
                    "metric-card-green"  if item["label"] == "Positive" else
                    "metric-card-orange" if item["label"] == "Negative" else ""
                )
                st.markdown(
                    f'<div class="metric-card {color}">'
                    f'{item.get("emoji", "😐")} <b>{item["label"]}</b> '
                    f'(score: {item["score"]:+.3f})<br>'
                    f'<small>"{item["comment"]}"</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Social Media
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📱 Social Media":
    st.subheader("📱 Social Media Snippets")
    st.caption(
        "Auto-generate platform-optimised posts for Twitter/X, LinkedIn, and Instagram "
        "from your blog draft. Includes engagement prediction."
    )

    if not _check_api_key():
        st.stop()

    if not st.session_state.blog_draft.get("content"):
        st.info("📝 Generate a blog draft first (**✏️ Write Blog**).")
        st.stop()

    draft   = st.session_state.blog_draft
    content = draft.get("content") or draft.get("raw", "")
    title   = draft.get("seo_title") or st.session_state.current_topic

    st.markdown(f"**Blog:** {title}")

    col1, col2 = st.columns(2)
    social_btn  = col1.button("📱 Generate Social Posts",        use_container_width=True)
    engage_btn  = col2.button("📊 Predict Engagement",           use_container_width=True)

    if social_btn:
        with st.spinner("IBM Granite is crafting social media posts…"):
            st.session_state.social_snippets = generate_social_snippets(
                title, content[:500], llm
            )

    if engage_btn:
        with st.spinner("Predicting engagement metrics…"):
            st.session_state.engagement_pred = predict_engagement(title, llm)

    # Social posts
    if st.session_state.social_snippets:
        st.markdown("---")
        snips = st.session_state.social_snippets
        s1, s2, s3 = st.columns(3)

        with s1:
            st.markdown("#### 🐦 Twitter / X")
            text = snips.get("twitter", "—")
            st.markdown(
                f'<div class="metric-card" style="min-height:110px">{text}</div>',
                unsafe_allow_html=True,
            )
            char_count = len(text)
            color = "🟢" if char_count <= 280 else "🔴"
            st.caption(f"{color} {char_count}/280 chars")
            st.download_button("Copy", data=text, file_name="tweet.txt",
                               mime="text/plain", key="dl_tw")

        with s2:
            st.markdown("#### 💼 LinkedIn")
            text = snips.get("linkedin", "—")
            st.markdown(
                f'<div class="metric-card" style="min-height:110px">{text}</div>',
                unsafe_allow_html=True,
            )
            st.download_button("Copy", data=text, file_name="linkedin.txt",
                               mime="text/plain", key="dl_li")

        with s3:
            st.markdown("#### 📸 Instagram")
            text = snips.get("instagram", "—")
            st.markdown(
                f'<div class="metric-card" style="min-height:110px">{text}</div>',
                unsafe_allow_html=True,
            )
            st.download_button("Copy", data=text, file_name="instagram.txt",
                               mime="text/plain", key="dl_ig")

    # Engagement prediction
    if st.session_state.engagement_pred:
        ep = st.session_state.engagement_pred
        st.markdown("---")
        st.markdown("### 📊 Engagement Prediction")

        e1, e2, e3, e4 = st.columns(4)
        e1.metric("🎯 Score",    f"{ep.get('score', '—')}/100")
        e2.metric("📅 Best Day", ep.get("best_day", "—"))
        e3.metric("⏰ Best Time", ep.get("best_time", "—"))
        e4.metric("📡 Reach",    ep.get("reach", "—"))

        st.plotly_chart(_engagement_bar(ep.get("score", 70)), use_container_width=True)

        if ep.get("reason"):
            st.info(f"💡 {ep['reason']}")
        if ep.get("content_type"):
            st.markdown(f"**📝 Content Type:** {ep['content_type']}")
        if ep.get("hashtags"):
            htags_html = " ".join(
                f'<span class="topic-chip">{t}</span>' for t in ep["hashtags"]
            )
            st.markdown("**#️⃣ Recommended Hashtags:**")
            st.markdown(htags_html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Settings
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.subheader("⚙️ Settings & Configuration")

    st.markdown("### 🔑 API & Model Configuration")
    st.info(
        "All credentials are loaded securely from environment variables. "
        "**Never paste API keys into this UI.**"
    )

    with st.expander("📋 Current Configuration"):
        st.markdown(f"- **Primary Model:** `{Config.WATSONX_MODEL_ID}` (IBM Granite)")
        st.markdown(f"- **Fallback Model:** `{Config.WATSONX_FALLBACK_MODEL}` (Llama 3.3 70B)")
        st.markdown(f"- **Active Model:** `{llm.active_model}`")
        st.markdown(f"- **Endpoint:** `{Config.WATSONX_ENDPOINT}`")
        st.markdown(f"- **Project ID:** `{Config.WATSONX_PROJECT_ID}`")
        st.markdown(f"- **API Key Set:** {'✅ Yes (hidden)' if Config.WATSONX_API_KEY else '❌ No'}")
        st.markdown(f"- **App Version:** `{Config.APP_VERSION}`")

    st.markdown("### 📰 Configured RSS Feeds")
    for name, url in Config.RSS_FEEDS.items():
        st.markdown(f"- **{name}:** [{url}]({url})")

    st.markdown("### 🛡️ Responsible AI Guardrails")
    st.markdown(
        "Content containing any of the following categories is **blocked** "
        "at both input and output stages:"
    )
    blocked_html = " ".join(
        f'<span class="topic-chip" style="background:#fde8e8;color:#b91c1c;border-color:#fca5a5">'
        f'{kw}</span>'
        for kw in Config.BLOCKED_KEYWORDS
    )
    st.markdown(blocked_html, unsafe_allow_html=True)

    st.markdown("### 📂 Environment Setup")
    st.code(
        "# Create a .env file in the blog_assistant/ directory:\n\n"
        "WATSONX_API_KEY=your_ibm_cloud_api_key\n"
        "WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121\n"
        "WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com\n"
        "WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct",
        language="bash",
    )

    st.markdown("### 📦 Publish Window Reference")
    pw_data = [
        {"Day": day, "Best Time": data["best_time"], "Base Score": data["base_score"]}
        for day, data in Config.PUBLISH_WINDOWS.items()
    ]
    st.dataframe(pd.DataFrame(pw_data), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">'
    '✍️ Writing Pulse AI &nbsp;·&nbsp; '
    'Powered by <b>IBM watsonx.ai</b> &amp; <b>IBM Granite LLM</b> &nbsp;·&nbsp; '
    f'v{Config.APP_VERSION} &nbsp;·&nbsp; For educational purposes only'
    '</div>',
    unsafe_allow_html=True,
)
