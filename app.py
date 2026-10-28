"""
app.py — AI Customer Support Chatbot
Streamlit frontend powered by IBM watsonx.ai (Llama 3.3 70B, au-syd)

Run with:  streamlit run app.py
"""

import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from core.watsonx_client import llm
from core.chatbot_engine import (
    get_bot_response,
    analyze_sentiment,
    generate_ticket,
    summarize_conversation,
    detect_intent,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Customer Support — IBM watsonx.ai",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main-header {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 60%, #0f62fe 100%);
    padding: 1.4rem 2rem; border-radius: 12px; margin-bottom: 1.2rem; color: white;
  }
  .main-header h1 { font-size: 1.8rem; margin: 0; }
  .main-header p  { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
  /* Chat bubbles */
  .bubble-user {
    background: #0f62fe; color: white;
    padding: 10px 15px; border-radius: 18px 18px 4px 18px;
    max-width: 75%; margin: 6px 0 6px auto; font-size: 0.9rem;
    word-wrap: break-word;
  }
  .bubble-bot {
    background: #f0f4f8; color: #161616; border: 1px solid #dde3ed;
    padding: 10px 15px; border-radius: 18px 18px 18px 4px;
    max-width: 80%; margin: 6px auto 6px 0; font-size: 0.9rem;
    word-wrap: break-word;
  }
  .bubble-system {
    background: #e8f5e9; color: #1b5e20; border: 1px solid #c8e6c9;
    padding: 8px 14px; border-radius: 8px;
    font-size: 0.82rem; text-align: center; margin: 6px auto;
  }
  .bubble-escalate {
    background: #fff3e0; color: #e65100; border: 1px solid #ffcc80;
    padding: 8px 14px; border-radius: 8px;
    font-size: 0.82rem; text-align: center; margin: 6px auto;
  }
  .msg-meta { font-size: 0.7rem; color: #8d8d8d; margin-top: 2px; }
  .intent-badge {
    display: inline-block; padding: 2px 10px; border-radius: 10px;
    font-size: 0.72rem; font-weight: 700;
  }
  .intent-billing   { background:#fff3cd; color:#856404; }
  .intent-technical { background:#d1ecf1; color:#0c5460; }
  .intent-account   { background:#d4edda; color:#155724; }
  .intent-general   { background:#f0f4f8; color:#525252; }
  .intent-escalation{ background:#fde8e8; color:#c53030; }
  .ticket-card {
    background: #f7f9fc; border: 1px solid #dde3ed;
    border-radius: 10px; padding: 1rem; margin: 0.5rem 0;
    font-size: 0.85rem;
  }
  .ibm-badge {
    display: inline-block; background: #0f62fe; color: white;
    border-radius: 20px; padding: 2px 12px; font-size: 0.72rem;
    font-weight: 700; letter-spacing: 0.4px;
  }
  .footer {
    text-align: center; padding: 1.2rem; color: #8d8d8d;
    font-size: 0.72rem; border-top: 1px solid #e5e7eb; margin-top: 1.5rem;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "messages":        [],   # {"role","content","meta":{intent,sentiment,ts}}
        "tickets":         [],   # list of ticket dicts
        "user_name":       "",
        "session_start":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "turn_count":      0,
        "escalated":       False,
        "sentiment_log":   [],   # list of {"turn","score","label"}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _check_api_key() -> bool:
    if not Config.WATSONX_API_KEY:
        st.error(
            "**WATSONX_API_KEY not set.**\n\n"
            "Add it to `.env`:\n```\nWATSONX_API_KEY=your_key_here\n```"
        )
        return False
    return True


_INTENT_COLORS = {
    "billing": "intent-billing", "technical": "intent-technical",
    "account": "intent-account", "general": "intent-general",
    "escalation": "intent-escalation", "blocked": "intent-escalation",
}

_INTENT_ICONS = {
    "billing": "💳", "technical": "🔧", "account": "👤",
    "general": "💬", "escalation": "🚨", "blocked": "🚫",
}


def _intent_badge(intent: str) -> str:
    css  = _INTENT_COLORS.get(intent, "intent-general")
    icon = _INTENT_ICONS.get(intent, "💬")
    return f'<span class="intent-badge {css}">{icon} {intent.capitalize()}</span>'


def _render_messages():
    """Render all chat messages as styled bubbles."""
    for msg in st.session_state.messages:
        role    = msg["role"]
        content = msg["content"]
        meta    = msg.get("meta", {})
        ts      = meta.get("ts", "")

        if role == "system":
            st.markdown(f'<div class="bubble-system">{content}</div>', unsafe_allow_html=True)
        elif role == "user":
            st.markdown(
                f'<div style="text-align:right">'
                f'<div class="bubble-user">{content}</div>'
                f'<div class="msg-meta">{ts}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        elif role == "assistant":
            intent    = meta.get("intent", "general")
            sentiment = meta.get("sentiment", {})
            badge     = _intent_badge(intent)
            sent_emoji = sentiment.get("emoji", "")

            if intent == "escalation":
                st.markdown(
                    f'<div class="bubble-escalate">🚨 Escalation triggered — Human agent notified</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div class="bubble-bot">'
                f'<b>🤖 {Config.BOT_NAME}</b><br>{content}'
                f'<br><div class="msg-meta">{badge} &nbsp; {sent_emoji} {sentiment.get("label","")} &nbsp; {ts}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _sentiment_trend_chart():
    """Line chart of sentiment score across conversation turns."""
    log = st.session_state.sentiment_log
    if len(log) < 2:
        return None
    df  = pd.DataFrame(log)
    fig = px.line(
        df, x="turn", y="score",
        title="Customer Sentiment Trend",
        markers=True,
        color_discrete_sequence=["#0f62fe"],
    )
    fig.add_hline(y=0,  line_dash="dot", line_color="#8d8d8d")
    fig.add_hrect(y0=0.15, y1=1,   fillcolor="#d4edda", opacity=0.15, line_width=0)
    fig.add_hrect(y0=-1,  y1=-0.15, fillcolor="#fde8e8", opacity=0.15, line_width=0)
    fig.update_layout(height=220, margin=dict(t=35,b=10,l=10,r=10),
                      xaxis_title="Turn", yaxis_title="Score",
                      yaxis=dict(range=[-1,1]))
    return fig


def _intent_donut():
    """Donut of intent distribution across conversation."""
    msgs = [m for m in st.session_state.messages if m["role"] == "assistant"]
    if not msgs:
        return None
    counts: dict[str, int] = {}
    for m in msgs:
        intent = m.get("meta", {}).get("intent", "general")
        counts[intent] = counts.get(intent, 0) + 1
    fig = px.pie(
        values=list(counts.values()),
        names=list(counts.keys()),
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Intent Distribution",
    )
    fig.update_layout(height=220, margin=dict(t=35,b=10,l=10,r=10),
                      showlegend=True, legend=dict(orientation="h"))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 Support Chatbot")
    st.markdown(
        f'<span class="ibm-badge">IBM watsonx.ai</span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Customer name
    name_input = st.text_input(
        "Your Name (optional):",
        value=st.session_state.user_name,
        placeholder="e.g. Jane Smith",
    )
    if name_input != st.session_state.user_name:
        st.session_state.user_name = name_input

    st.markdown("---")

    # Session stats
    bot_msgs  = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
    user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
    st.markdown("### 📊 Session Stats")
    st.metric("Turns",         st.session_state.turn_count)
    st.metric("Your Messages", user_msgs)
    st.metric("Bot Replies",   bot_msgs)
    st.metric("Tickets Open",  len(st.session_state.tickets))

    st.markdown("---")

    # Clear / New session
    if st.button("🔄 New Conversation", use_container_width=True):
        for k in ["messages","tickets","turn_count","escalated","sentiment_log"]:
            st.session_state[k] = [] if k != "turn_count" else 0
            if k == "escalated":
                st.session_state[k] = False
        st.session_state.session_start = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.rerun()

    if st.button("🎫 Generate Summary Ticket", use_container_width=True,
                 disabled=not bool(st.session_state.messages)):
        if _check_api_key():
            with st.spinner("Summarizing conversation…"):
                conv = [{"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                        if m["role"] in ("user","assistant")]
                summary = summarize_conversation(conv, llm)
            last_intent = "general"
            for m in reversed(st.session_state.messages):
                if m["role"] == "assistant":
                    last_intent = m.get("meta", {}).get("intent", "general")
                    break
            last_sentiment = analyze_sentiment(
                " ".join(m["content"] for m in st.session_state.messages if m["role"] == "user")
            )
            ticket = generate_ticket(
                st.session_state.user_name,
                summary,
                last_intent,
                last_sentiment,
            )
            st.session_state.tickets.append(ticket)
            st.success(f"Ticket created: {ticket['ticket_id']}")

    st.markdown("---")
    st.markdown(
        f"**Model:** `{Config.WATSONX_MODEL_ID}`\n\n"
        f"**Region:** au-syd\n\n"
        f"**Status:** " + ("🟢 Ready" if Config.WATSONX_API_KEY else "🔴 No API key"),
    )
    st.caption(f"Session started: {st.session_state.session_start}")


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    f'<h1>🤖 {Config.BOT_NAME} — AI Customer Support</h1>'
    f'<p>{Config.COMPANY} &nbsp;·&nbsp; Powered by IBM watsonx.ai &amp; Llama 3.3 70B &nbsp;·&nbsp; Available 24/7</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Main layout: Chat | Dashboard
# ─────────────────────────────────────────────────────────────────────────────
chat_col, dash_col = st.columns([3, 2], gap="large")


# ══════════════════════════════════════════════════════════════════════════════
# LEFT: Chat Panel
# ══════════════════════════════════════════════════════════════════════════════
with chat_col:
    st.markdown("### 💬 Chat with Aria")

    # Welcome message on first load
    if not st.session_state.messages:
        welcome = (
            f"Hello{' ' + st.session_state.user_name if st.session_state.user_name else ''}! "
            f"I'm **{Config.BOT_NAME}**, your AI support assistant for {Config.COMPANY}. "
            "How can I help you today?\n\n"
            "You can ask me about:\n"
            "- 🔐 Password reset & account access\n"
            "- 📦 Order tracking & returns\n"
            "- 💳 Billing & subscriptions\n"
            "- 🔧 Technical issues\n"
            "- 📞 Speaking to a human agent"
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome,
            "meta": {"intent": "general", "sentiment": {"label":"Neutral","emoji":"😐"}, "ts": datetime.now().strftime("%H:%M")},
        })

    # Chat message area
    chat_container = st.container(height=480, border=True)
    with chat_container:
        _render_messages()

    # Quick reply chips
    st.markdown("**Quick replies:**")
    chip_cols = st.columns(4)
    quick = [
        "Reset my password",
        "Track my order",
        "Cancel subscription",
        "Speak to an agent",
    ]
    for i, chip_col in enumerate(chip_cols):
        if chip_col.button(quick[i], key=f"chip_{i}", use_container_width=True):
            st.session_state["_quick_input"] = quick[i]

    # Input row
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Type your message:",
            value=st.session_state.pop("_quick_input", ""),
            placeholder="Describe your issue…",
            label_visibility="collapsed",
        )
        send = st.form_submit_button("Send ➤", use_container_width=True)

    if send and user_input.strip():
        if not _check_api_key():
            st.stop()

        msg = user_input.strip()
        ts  = datetime.now().strftime("%H:%M")

        # Add user message
        st.session_state.messages.append({
            "role": "user", "content": msg,
            "meta": {"ts": ts},
        })
        st.session_state.turn_count += 1

        # Build conversation history for LLM
        conv_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] in ("user", "assistant")
        ][:-1]  # exclude the message we just added (it's the user_msg)

        # Get bot response
        with st.spinner("Aria is typing…"):
            result = get_bot_response(
                user_msg=msg,
                conversation=conv_history,
                user_name=st.session_state.user_name,
                llm=llm,
            )

        # Log sentiment
        st.session_state.sentiment_log.append({
            "turn":  st.session_state.turn_count,
            "score": result["sentiment"]["score"],
            "label": result["sentiment"]["label"],
        })

        # Add bot reply
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["reply"],
            "meta": {
                "intent":    result["intent"],
                "sentiment": result["sentiment"],
                "faq":       result["faq_matched"],
                "ts":        datetime.now().strftime("%H:%M"),
            },
        })

        # Escalation flag
        if result["escalate"] and not st.session_state.escalated:
            st.session_state.escalated = True

        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT: Dashboard Panel
# ══════════════════════════════════════════════════════════════════════════════
with dash_col:
    dash_tab1, dash_tab2, dash_tab3 = st.tabs(["📊 Analytics", "🎫 Tickets", "📚 FAQ"])

    # ── Analytics ─────────────────────────────────────────────────────────────
    with dash_tab1:
        st.markdown("#### 📊 Live Analytics")

        # Current sentiment
        user_text = " ".join(
            m["content"] for m in st.session_state.messages if m["role"] == "user"
        )
        overall_sent = analyze_sentiment(user_text) if user_text else {"label":"—","emoji":"😐","score":0,"color":"#8d8d8d"}
        sent_col, intent_col = st.columns(2)
        sent_col.markdown("**Overall Sentiment**")
        sent_col.markdown(
            f'<div style="font-size:2rem;text-align:center;">{overall_sent["emoji"]}</div>'
            f'<div style="text-align:center;font-weight:700;color:{overall_sent["color"]}">'
            f'{overall_sent["label"]}</div>',
            unsafe_allow_html=True,
        )

        # Last intent
        last_intent = "—"
        for m in reversed(st.session_state.messages):
            if m["role"] == "assistant" and m.get("meta", {}).get("intent"):
                last_intent = m["meta"]["intent"].capitalize()
                break
        intent_col.markdown("**Last Intent**")
        intent_col.markdown(
            f'<div style="font-size:2rem;text-align:center;">'
            f'{_INTENT_ICONS.get(last_intent.lower(),"💬")}</div>'
            f'<div style="text-align:center;font-weight:700">{last_intent}</div>',
            unsafe_allow_html=True,
        )

        # Sentiment trend
        trend = _sentiment_trend_chart()
        if trend:
            st.plotly_chart(trend, use_container_width=True)
        else:
            st.info("Sentiment trend will appear after a few messages.")

        # Intent donut
        donut = _intent_donut()
        if donut:
            st.plotly_chart(donut, use_container_width=True)

        # Escalation status
        if st.session_state.escalated:
            st.warning("🚨 **Escalation active** — Human agent notified.")

        # FAQ match count
        faq_count = sum(
            1 for m in st.session_state.messages
            if m["role"] == "assistant" and m.get("meta", {}).get("faq")
        )
        if faq_count:
            st.success(f"✅ {faq_count} question(s) answered from FAQ knowledge base")

    # ── Tickets ────────────────────────────────────────────────────────────────
    with dash_tab2:
        st.markdown("#### 🎫 Support Tickets")
        if not st.session_state.tickets:
            st.info("No tickets yet. Click **Generate Summary Ticket** in the sidebar after your conversation.")
        for ticket in reversed(st.session_state.tickets):
            priority_color = "#da1e28" if ticket["priority"] == "High" else "#24a148"
            st.markdown(
                f'<div class="ticket-card">'
                f'<b>🎫 {ticket["ticket_id"]}</b> &nbsp;'
                f'<span style="color:{priority_color};font-weight:700">{ticket["priority"]} Priority</span><br>'
                f'<b>Customer:</b> {ticket["customer"]} &nbsp;|&nbsp; '
                f'<b>Intent:</b> {ticket["intent"]} &nbsp;|&nbsp; '
                f'<b>Status:</b> {ticket["status"]}<br>'
                f'<b>Created:</b> {ticket["created_at"]}<br>'
                f'<b>Summary:</b> {ticket["summary"]}'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Download ticket as JSON
            st.download_button(
                "⬇️ Download Ticket",
                data=json.dumps(ticket, indent=2),
                file_name=f"{ticket['ticket_id']}.json",
                mime="application/json",
                key=f"dl_{ticket['ticket_id']}",
            )

    # ── FAQ ────────────────────────────────────────────────────────────────────
    with dash_tab3:
        st.markdown("#### 📚 FAQ Knowledge Base")
        for question, answer in Config.FAQ.items():
            with st.expander(f"❓ {question}"):
                st.write(answer)


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="footer">'
    f'🤖 {Config.BOT_NAME} · {Config.COMPANY} · Powered by IBM watsonx.ai · '
    f'Llama 3.3 70B Instruct (au-syd) · Available 24/7'
    f'</div>',
    unsafe_allow_html=True,
)
