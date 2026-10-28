"""
app.py — Writing Pulse: AI Blogging Assistant
Streamlit frontend powered by IBM watsonx.ai (Llama 3.3 70B, au-syd)

Run with:  streamlit run app.py
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from PIL import Image
import io

# ── path setup so sub-modules resolve correctly ───────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from watsonx_client import llm
from agents.research_agent  import fetch_rss_articles, fetch_top_headlines, summarize_research
from agents.trend_agent     import get_trending_topics, suggest_blog_topics, predict_engagement
from agents.content_agent   import generate_blog_draft, generate_social_snippets, process_voice_input
from agents.editorial_agent import review_draft, analyze_audience_comments, human_approval_check

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Writing Pulse — AI Blogging Assistant",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Main header */
  .main-header {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 60%, #0f62fe 100%);
    padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
    color: white;
  }
  .main-header h1 { font-size: 2rem; margin: 0; }
  .main-header p  { margin: 0.3rem 0 0; opacity: 0.82; font-size: 0.95rem; }
  /* Cards */
  .metric-card {
    background: #f7f9fc; border: 1px solid #dde3ed;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem;
  }
  /* Topic chips */
  .topic-chip {
    display: inline-block; background: #e8f1ff; color: #0f62fe;
    border: 1px solid #c0d4f5; border-radius: 16px;
    padding: 3px 12px; font-size: 0.8rem; margin: 3px;
  }
  /* Section labels */
  .section-label {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; color: #525252; margin-bottom: 4px;
  }
  /* Verdict badges */
  .verdict-approve  { color: #24a148; font-weight: 700; }
  .verdict-revision { color: #f1620a; font-weight: 700; }
  .verdict-major    { color: #da1e28; font-weight: 700; }
  /* IBM badge */
  .ibm-badge {
    display: inline-block; background: #0f62fe; color: white;
    border-radius: 20px; padding: 3px 12px; font-size: 0.72rem;
    font-weight: 700; letter-spacing: 0.4px; margin-left: 10px;
  }
  /* Footer */
  .footer {
    text-align: center; padding: 1.5rem; color: #8d8d8d;
    font-size: 0.75rem; border-top: 1px solid #e5e7eb; margin-top: 2rem;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "research_articles":  [],
        "research_summary":   "",
        "trending_topics":    [],
        "topic_suggestions":  [],
        "blog_draft":         {},
        "review_result":      {},
        "engagement_pred":    {},
        "social_snippets":    {},
        "sentiment_result":   {},
        "approval_status":    None,
        "current_topic":      "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _check_api_key() -> bool:
    if not Config.WATSONX_API_KEY:
        st.error(
            "⚠️ **WATSONX_API_KEY not configured.**\n\n"
            "Add your IBM Cloud API key to the `.env` file:\n"
            "```\nWATSONX_API_KEY=your_key_here\n```\n"
            "Then restart Streamlit."
        )
        return False
    return True


def _score_gauge(score: int, title: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 10]},
            "bar":  {"color": "#0f62fe"},
            "steps": [
                {"range": [0, 4],  "color": "#fde8e8"},
                {"range": [4, 7],  "color": "#fff3cd"},
                {"range": [7, 10], "color": "#d4edda"},
            ],
        },
    ))
    fig.update_layout(height=180, margin=dict(t=30, b=10, l=10, r=10))
    return fig


def _sentiment_donut(pos: int, neg: int, neu: int):
    fig = px.pie(
        values=[pos, neg, neu],
        names=["Positive", "Negative", "Neutral"],
        color_discrete_sequence=["#24a148", "#da1e28", "#8d8d8d"],
        hole=0.55,
    )
    fig.update_layout(height=240, margin=dict(t=10, b=10, l=10, r=10),
                      showlegend=True, legend=dict(orientation="h"))
    return fig


def _engagement_bar(score: int):
    color = "#24a148" if score >= 70 else "#f1620a" if score >= 40 else "#da1e28"
    fig = go.Figure(go.Bar(
        x=[score], y=["Engagement"], orientation="h",
        marker_color=color, text=[f"{score}/100"], textposition="inside",
    ))
    fig.update_layout(height=100, margin=dict(t=5, b=5, l=5, r=5),
                      xaxis=dict(range=[0, 100], showgrid=False),
                      yaxis=dict(showticklabels=False))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✍️ Writing Pulse")
    st.markdown(
        f'<span class="ibm-badge">IBM Granite / Llama 3.3 70B</span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio(
        "Go to",
        [
            "📊 Dashboard",
            "🔍 Research & Trends",
            "✏️ Write Blog",
            "🎯 Editorial Review",
            "💬 Audience Insights",
            "📱 Social Media",
            "⚙️ Settings",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        "**Model:** `meta-llama/llama-3-3-70b-instruct`\n\n"
        "**Region:** IBM Cloud au-syd\n\n"
        "**Status:** " + ("🟢 API key set" if Config.WATSONX_API_KEY else "🔴 No API key"),
    )
    st.markdown("---")
    st.caption("© 2024 Writing Pulse AI · IBM watsonx.ai")


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    '<h1>✍️ Writing Pulse</h1>'
    '<p>Agentic AI Blogging Assistant · Powered by IBM watsonx.ai &amp; Meta Llama 3.3 70B</p>'
    '</div>',
    unsafe_allow_html=True,
)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.subheader("📊 Writing Pulse Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔥 Trending Topics", len(st.session_state.trending_topics) or "—")
    col2.metric("📰 Articles Found", len(st.session_state.research_articles) or "—")
    col3.metric("📝 Draft Status",
                "Ready" if st.session_state.blog_draft.get("content") else "Not started")
    col4.metric("✅ Approval",
                st.session_state.approval_status or "Pending")

    st.markdown("---")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("### 🔥 Latest Headlines")
        if st.button("🔄 Fetch Headlines", use_container_width=True):
            with st.spinner("Fetching latest news…"):
                headlines = fetch_top_headlines(max_articles=8)
                st.session_state["_headlines"] = headlines

        for h in st.session_state.get("_headlines", []):
            st.markdown(
                f'<div class="metric-card">'
                f'<b>{h["title"]}</b><br>'
                f'<small>📰 {h["source"]} &nbsp;·&nbsp; <a href="{h["url"]}" target="_blank">Read</a></small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("### 📈 Trending Keywords")
        if st.button("🔄 Fetch Trends", use_container_width=True):
            with st.spinner("Analyzing trends…"):
                st.session_state.trending_topics = get_trending_topics()

        if st.session_state.trending_topics:
            df = pd.DataFrame(st.session_state.trending_topics[:10])
            fig = px.bar(
                df, x="count", y="keyword", orientation="h",
                color="count", color_continuous_scale="Blues",
                title="Keyword Frequency Across News Feeds",
            )
            fig.update_layout(height=320, margin=dict(t=30, b=10, l=10, r=10),
                              coloraxis_showscale=False,
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Click 'Fetch Trends' to load trending keywords.")

    st.markdown("---")
    st.markdown("### 💡 Quick Start")
    qcol1, qcol2, qcol3 = st.columns(3)
    qcol1.info("**Step 1** → 🔍 Research & Trends\nFetch real-time articles and trending topics")
    qcol2.info("**Step 2** → ✏️ Write Blog\nGenerate an SEO-optimised draft with AI")
    qcol3.info("**Step 3** → 🎯 Editorial Review\nAI review + human approval before publishing")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Research & Trends
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Research & Trends":
    st.subheader("🔍 Research & Trend Analysis")

    tab1, tab2 = st.tabs(["🔬 Research Topic", "📈 Trending Topics"])

    # ── Research tab ─────────────────────────────────────────────────────────
    with tab1:
        topic = st.text_input("Enter a topic to research:", placeholder="e.g. Artificial Intelligence in Healthcare")
        col1, col2 = st.columns([1, 4])
        fetch_btn    = col1.button("🔍 Fetch Articles", use_container_width=True)
        summarize_btn = col2.button("🧠 Summarize with AI", use_container_width=True,
                                    disabled=not bool(st.session_state.research_articles))

        if fetch_btn and topic:
            with st.spinner(f"Searching news feeds for '{topic}'…"):
                articles = fetch_rss_articles(topic)
                st.session_state.research_articles = articles
                st.session_state.current_topic     = topic
            st.success(f"Found {len(articles)} articles.")

        if summarize_btn:
            if not _check_api_key():
                st.stop()
            with st.spinner("AI is synthesizing research…"):
                summary = summarize_research(
                    st.session_state.research_articles,
                    st.session_state.current_topic,
                    llm,
                )
                st.session_state.research_summary = summary

        # Show articles
        if st.session_state.research_articles:
            st.markdown(f"**{len(st.session_state.research_articles)} articles found for:** `{st.session_state.current_topic}`")
            for i, art in enumerate(st.session_state.research_articles[:10]):
                with st.expander(f"[{i+1}] {art['title']} — {art['source']}"):
                    st.write(art["summary"])
                    st.markdown(f"[🔗 Read full article]({art['url']})")
                    st.caption(f"Published: {art['published']}")

        # Show summary
        if st.session_state.research_summary:
            st.markdown("---")
            st.markdown("### 🧠 AI Research Summary")
            st.markdown(
                f'<div class="metric-card">{st.session_state.research_summary}</div>',
                unsafe_allow_html=True,
            )

    # ── Trending tab ──────────────────────────────────────────────────────────
    with tab2:
        col1, col2 = st.columns([1, 3])
        if col1.button("🔄 Refresh Trends", use_container_width=True):
            with st.spinner("Scanning news feeds…"):
                st.session_state.trending_topics = get_trending_topics()

        if col2.button("💡 Suggest Blog Topics (AI)", use_container_width=True,
                       disabled=not bool(st.session_state.trending_topics)):
            if not _check_api_key():
                st.stop()
            with st.spinner("Generating blog topic ideas…"):
                st.session_state.topic_suggestions = suggest_blog_topics(
                    st.session_state.trending_topics, llm
                )

        if st.session_state.trending_topics:
            st.markdown("#### 🔥 Trending Keywords")
            chips_html = " ".join(
                f'<span class="topic-chip">#{t["keyword"]} ({t["count"]})</span>'
                for t in st.session_state.trending_topics
            )
            st.markdown(chips_html, unsafe_allow_html=True)

            st.markdown("#### 📋 Supporting Headlines")
            for t in st.session_state.trending_topics[:5]:
                with st.expander(f"#{t['keyword']} — {t['count']} mentions"):
                    for h in t["headlines"]:
                        st.write(f"• {h}")

        if st.session_state.topic_suggestions:
            st.markdown("---")
            st.markdown("#### 💡 AI-Suggested Blog Topics")
            for i, s in enumerate(st.session_state.topic_suggestions):
                with st.expander(f"💡 {s.get('title', f'Topic {i+1}')}"):
                    st.write(f"**Description:** {s.get('description', '')}")
                    st.write(f"**Target Audience:** {s.get('audience', '')}")
                    tags = " ".join(s.get("hashtags", []))
                    st.write(f"**Hashtags:** {tags}")
                    if st.button(f"Use this topic →", key=f"use_topic_{i}"):
                        st.session_state.current_topic = s.get("title", "")
                        st.success(f"Topic set to: **{s.get('title')}**. Go to ✏️ Write Blog.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Write Blog
# ═════════════════════════════════════════════════════════════════════════════
elif page == "✏️ Write Blog":
    st.subheader("✏️ Blog Draft Generator")

    if not _check_api_key():
        st.stop()

    # ── Input controls ────────────────────────────────────────────────────────
    with st.form("blog_form"):
        st.markdown("#### 📝 Blog Settings")
        col1, col2 = st.columns(2)

        topic = col1.text_input(
            "Blog Topic *",
            value=st.session_state.current_topic,
            placeholder="e.g. How AI is Transforming Healthcare in 2025",
        )
        tone = col2.selectbox(
            "Writing Tone",
            ["Professional", "Conversational", "Educational", "Persuasive",
             "Storytelling", "Technical", "Inspirational"],
        )
        word_count = col1.slider("Target Word Count", 300, 2000, 800, 100)
        col2.markdown("&nbsp;")

        st.markdown("#### 🔍 Research Context")
        research_ctx = st.text_area(
            "Paste research summary or key points (auto-filled if you ran research):",
            value=st.session_state.research_summary,
            height=120,
            placeholder="Paste any notes, data points, or context for the AI to use…",
        )

        st.markdown("#### 📎 Additional Inputs")
        input_tab1, input_tab2, input_tab3 = st.tabs(["📝 Text Notes", "🖼️ Image Description", "🎤 Voice Input"])

        with input_tab1:
            extra_text = st.text_area("Additional notes / author instructions:", height=80)

        with input_tab2:
            uploaded_img = st.file_uploader("Upload an image (we'll describe it for context):", type=["png","jpg","jpeg"])
            img_desc = ""
            if uploaded_img:
                img = Image.open(uploaded_img)
                st.image(img, caption="Uploaded image", width=300)
                img_desc = st.text_input("Describe what this image shows (for AI context):",
                                         placeholder="e.g. A chart showing AI adoption rates 2020-2025")

        with input_tab3:
            audio_file = st.file_uploader("Upload a voice note (.wav):", type=["wav"])
            voice_text = ""
            if audio_file:
                voice_text = process_voice_input(audio_file)
                st.info(f"Transcribed: {voice_text}")

        extra_context = "\n".join(filter(None, [extra_text, img_desc, voice_text]))

        generate_btn = st.form_submit_button("🚀 Generate Blog Draft", use_container_width=True)

    if generate_btn:
        if not topic:
            st.error("Please enter a blog topic.")
        else:
            with st.spinner("AI is writing your blog draft…"):
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

    # ── Display draft ─────────────────────────────────────────────────────────
    if st.session_state.blog_draft:
        draft = st.session_state.blog_draft

        if "error" in draft:
            st.error(draft["error"])
        else:
            st.markdown("---")
            st.markdown("### 📄 Generated Blog Draft")

            # Meta
            col1, col2 = st.columns([2, 1])
            col1.markdown(f"**SEO Title:** {draft.get('seo_title', '')}")
            col1.markdown(f"**Meta Description:** {draft.get('meta_description', '')}")
            tags_html = " ".join(
                f'<span class="topic-chip">{t}</span>'
                for t in draft.get("suggested_tags", [])
            )
            col1.markdown(tags_html, unsafe_allow_html=True)

            # Predict engagement
            if col2.button("📊 Predict Engagement", use_container_width=True):
                with st.spinner("Predicting engagement…"):
                    st.session_state.engagement_pred = predict_engagement(
                        draft.get("seo_title") or st.session_state.current_topic, llm
                    )

            if st.session_state.engagement_pred:
                ep = st.session_state.engagement_pred
                col2.plotly_chart(_engagement_bar(ep.get("score", 70)),
                                  use_container_width=True)
                col2.markdown(
                    f"📅 **Best:** {ep.get('best_day')} @ {ep.get('best_time')}\n\n"
                    f"💬 {ep.get('reason', '')}"
                )

            st.markdown("---")
            st.markdown("#### 📝 Blog Content")
            content = draft.get("content") or draft.get("raw", "")
            st.markdown(content)

            # Download
            st.download_button(
                "⬇️ Download as Markdown",
                data=f"# {draft.get('seo_title','Blog Post')}\n\n{content}",
                file_name="blog_draft.md",
                mime="text/markdown",
                use_container_width=True,
            )

            # Link suggestions
            if draft.get("link_suggestions"):
                st.markdown("**🔗 Link Suggestions:**")
                for ls in draft["link_suggestions"]:
                    st.write(f"• {ls}")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Editorial Review
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Editorial Review":
    st.subheader("🎯 AI Editorial Review & Human Approval")

    if not _check_api_key():
        st.stop()

    if not st.session_state.blog_draft.get("content"):
        st.info("📝 No draft yet. Go to **✏️ Write Blog** to generate one first.")
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
        with st.spinner("AI editor is reviewing your draft…"):
            review = review_draft(draft_content, topic, llm)
            st.session_state.review_result = review
            approved, msg = human_approval_check(review)
            st.session_state.approval_status = "Approved ✅" if approved else "Needs Revision ⚠️"

    if st.session_state.review_result:
        review = st.session_state.review_result

        if "error" in review:
            st.error(review["error"])
        else:
            # ── Score gauges ─────────────────────────────────────────────────
            st.markdown("### 📊 Quality Scores")
            g1, g2, g3 = st.columns(3)
            g1.plotly_chart(_score_gauge(review["readability"], "Readability"), use_container_width=True)
            g2.plotly_chart(_score_gauge(review["seo"],         "SEO"),         use_container_width=True)
            g3.plotly_chart(_score_gauge(review["engagement"],  "Engagement"),  use_container_width=True)

            # ── Verdict ───────────────────────────────────────────────────────
            verdict = review.get("verdict", "")
            approved, approval_msg = human_approval_check(review)
            st.markdown("---")
            st.markdown(f"### Verdict: {verdict}")
            if approved:
                st.success(approval_msg)
            else:
                st.warning(approval_msg)

            # ── Details ────────────────────────────────────────────────────
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ✅ Strengths")
                for s in review.get("strengths", []):
                    st.write(f"• {s}")
            with c2:
                st.markdown("#### 🔧 Improvements Needed")
                for imp in review.get("improvements", []):
                    st.write(f"• {imp}")

            if review.get("fact_flags"):
                st.markdown("#### ⚠️ Fact-Check Flags")
                for flag in review["fact_flags"]:
                    st.warning(f"⚠️ {flag}")

            # ── Human approval gate ────────────────────────────────────────
            st.markdown("---")
            st.markdown("### 🧑 Human Approval Gate")
            st.info("Review the AI feedback above, then make the final publishing decision.")
            hcol1, hcol2 = st.columns(2)
            if hcol1.button("✅ Approve for Publishing", use_container_width=True):
                st.session_state.approval_status = "Approved ✅"
                st.success("✅ Draft approved for publishing!")
                st.balloons()
            if hcol2.button("❌ Send Back for Revision", use_container_width=True):
                st.session_state.approval_status = "Needs Revision ⚠️"
                st.warning("Draft sent back for revision.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Audience Insights
# ═════════════════════════════════════════════════════════════════════════════
elif page == "💬 Audience Insights":
    st.subheader("💬 Audience Sentiment Analysis")

    st.markdown("Paste audience comments, social media replies, or feedback below:")
    comments_input = st.text_area(
        "Comments (one per line):",
        height=180,
        placeholder="Great article! Very helpful.\nToo long and boring.\nThis changed my perspective entirely.\nNot sure I agree with point 3…",
    )

    if st.button("📊 Analyze Sentiment", use_container_width=False):
        comments = [c.strip() for c in comments_input.splitlines() if c.strip()]
        if not comments:
            st.warning("Please enter at least one comment.")
        else:
            with st.spinner("Analyzing sentiment…"):
                result = analyze_audience_comments(comments)
                st.session_state.sentiment_result = result

    if st.session_state.sentiment_result:
        r = st.session_state.sentiment_result

        # ── Overview metrics ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### Overall: {r['overall']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Comments", r["total"])
        m2.metric("😊 Positive",     r["pos_count"])
        m3.metric("😟 Negative",     r["neg_count"])
        m4.metric("😐 Neutral",      r["neu_count"])

        # ── Donut chart ───────────────────────────────────────────────────────
        col1, col2 = st.columns([1, 2])
        col1.plotly_chart(
            _sentiment_donut(r["pos_count"], r["neg_count"], r["neu_count"]),
            use_container_width=True,
        )

        # ── Per-comment breakdown ─────────────────────────────────────────────
        with col2:
            st.markdown("#### Per-Comment Breakdown")
            for item in r.get("breakdown", []):
                emoji = item.get("emoji", "😐")
                label = item.get("label", "Neutral")
                comment = item.get("comment", "")
                score   = item.get("score", 0)
                st.markdown(
                    f'<div class="metric-card">'
                    f'{emoji} <b>{label}</b> (score: {score:+.2f})<br>'
                    f'<small>{comment}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Social Media
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📱 Social Media":
    st.subheader("📱 Social Media Snippets Generator")

    if not _check_api_key():
        st.stop()

    if not st.session_state.blog_draft.get("content"):
        st.info("📝 Generate a blog draft first (✏️ Write Blog).")
        st.stop()

    draft   = st.session_state.blog_draft
    content = draft.get("content") or draft.get("raw", "")
    title   = draft.get("seo_title") or st.session_state.current_topic

    st.markdown(f"**Blog:** {title}")

    if st.button("📱 Generate Social Media Posts", use_container_width=False):
        with st.spinner("Crafting social media posts…"):
            st.session_state.social_snippets = generate_social_snippets(
                title, content[:500], llm
            )

    if st.session_state.social_snippets:
        snips = st.session_state.social_snippets
        st.markdown("---")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🐦 Twitter / X")
            st.markdown(
                f'<div class="metric-card" style="min-height:100px">{snips.get("twitter","—")}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"{len(snips.get('twitter',''))} / 280 chars")

        with c2:
            st.markdown("#### 💼 LinkedIn")
            st.markdown(
                f'<div class="metric-card" style="min-height:100px">{snips.get("linkedin","—")}</div>',
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown("#### 📸 Instagram")
            st.markdown(
                f'<div class="metric-card" style="min-height:100px">{snips.get("instagram","—")}</div>',
                unsafe_allow_html=True,
            )

        # ── Engagement prediction ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📊 Predicted Engagement")
        if st.button("🔮 Predict Blog Engagement", use_container_width=False):
            with st.spinner("Predicting engagement metrics…"):
                st.session_state.engagement_pred = predict_engagement(title, llm)

        if st.session_state.engagement_pred:
            ep = st.session_state.engagement_pred
            e1, e2, e3 = st.columns(3)
            e1.metric("Engagement Score", f"{ep.get('score', '—')}/100")
            e2.metric("Best Day", ep.get("best_day", "—"))
            e3.metric("Best Time", ep.get("best_time", "—"))
            st.info(f"💡 {ep.get('reason', '')}")
            htags = " ".join(ep.get("hashtags", []))
            if htags:
                st.markdown(f"**Hashtags:** {htags}")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Settings
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.subheader("⚙️ Settings & Configuration")

    st.markdown("### 🔑 API Configuration")
    st.markdown(
        "Credentials are loaded securely from environment variables. "
        "**Never paste API keys directly into this UI.**"
    )

    with st.expander("📋 Current Configuration (no secrets shown)"):
        st.markdown(f"- **Model:** `{Config.WATSONX_MODEL_ID}`")
        st.markdown(f"- **Endpoint:** `{Config.WATSONX_ENDPOINT}`")
        st.markdown(f"- **Project ID:** `{Config.WATSONX_PROJECT_ID}`")
        st.markdown(f"- **API Key Set:** {'✅ Yes' if Config.WATSONX_API_KEY else '❌ No'}")

    st.markdown("### 📰 Configured RSS Feeds")
    for name, url in Config.RSS_FEEDS.items():
        st.markdown(f"- **{name}:** [{url}]({url})")

    st.markdown("### 🛡️ Responsible AI Guardrails")
    st.markdown("The following content types are blocked by the content guardrails:")
    blocked = ", ".join(f"`{k}`" for k in Config.BLOCKED_KEYWORDS)
    st.markdown(blocked)

    st.markdown("### 📂 .env Setup Instructions")
    st.code(
        "# Create a .env file in the blog_assistant/ directory:\n"
        "WATSONX_API_KEY=your_ibm_api_key_here\n"
        "WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121\n"
        "WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com\n"
        "WATSONX_MODEL_ID=meta-llama/llama-3-3-70b-instruct",
        language="bash",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">'
    '✍️ Writing Pulse AI &nbsp;·&nbsp; Powered by IBM watsonx.ai &nbsp;·&nbsp; '
    'Meta Llama 3.3 70B Instruct (au-syd) &nbsp;·&nbsp; '
    'For educational purposes only'
    '</div>',
    unsafe_allow_html=True,
)
