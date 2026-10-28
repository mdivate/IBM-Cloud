# 🤖 AI Customer Support Chatbot — Powered by IBM watsonx.ai

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-ff4b4b?logo=streamlit)](https://streamlit.io)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe?logo=ibm)](https://www.ibm.com/watsonx)
[![LLM](https://img.shields.io/badge/LLM-Llama%203.3%2070B-orange?logo=meta)](https://ai.meta.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Project 5** — An AI-powered customer support chatbot built with **Streamlit** and **IBM watsonx.ai**, using **Meta Llama 3.3 70B Instruct** (Sydney region). Features real-time sentiment analysis, intent detection, FAQ matching, human escalation, automated ticket generation, and a live analytics dashboard.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **AI Chat (Aria)** | Multi-turn conversational support agent with memory across the session |
| 🎯 **Intent Detection** | Classifies every message: Billing · Technical · Account · Escalation · General |
| 📚 **FAQ Knowledge Base** | Instant answers to 8 common questions (no LLM call needed) |
| 🚨 **Human Escalation** | Detects escalation keywords and flags the session for a human agent |
| 😊 **Sentiment Analysis** | Per-message lexicon-based sentiment with live trend chart |
| 🎫 **Ticket Generation** | AI-summarizes the conversation and creates a downloadable JSON ticket |
| 📊 **Live Dashboard** | Real-time sentiment trend, intent donut chart, session stats |
| 🛡️ **Responsible AI** | Input guardrails block 9 harmful/adversarial topics |
| ⚡ **Quick Replies** | One-click chips for the most common support requests |

---

## 🏗️ Project Structure

```
support_chatbot/
├── app.py                      # Streamlit frontend — chat UI + live dashboard
├── config.py                   # Centralised config — secrets from env vars only
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template (safe to commit)
├── .env                        # Your actual secrets (git-ignored)
└── core/
    ├── __init__.py
    ├── watsonx_client.py       # IBM IAM auth + multi-turn Llama 3 LLM client
    └── chatbot_engine.py       # Intent detection, FAQ, sentiment, guardrails, tickets
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- IBM Cloud account with **watsonx.ai** access
- IBM watsonx.ai **Project ID** and **API Key**

### 1. Clone the repository

```bash
git clone https://github.com/mdivate/IBM-Cloud.git
cd IBM-Cloud
git checkout support-chatbot
cd support_chatbot
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
WATSONX_API_KEY=your_ibm_api_key_here
WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121
WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com
WATSONX_MODEL_ID=meta-llama/llama-3-3-70b-instruct
```

### 5. Run the chatbot

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## ⚙️ Configuration

| Variable | Description | Default |
|---|---|---|
| `WATSONX_API_KEY` | IBM Cloud API Key | *(required)* |
| `WATSONX_PROJECT_ID` | watsonx.ai Project ID | `280ea383-d47b-42ab-a981-b28f66296121` |
| `WATSONX_ENDPOINT` | Regional endpoint | `https://au-syd.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | Foundation model ID | `meta-llama/llama-3-3-70b-instruct` |

---

## 🧠 Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  Streamlit Web UI  (app.py)                   │
│                                                               │
│   Chat Panel (left)          │   Dashboard (right)           │
│   ─────────────────────      │   ─────────────────────       │
│   • Chat bubbles (Aria)      │   • Sentiment trend chart     │
│   • Quick reply chips        │   • Intent donut chart        │
│   • Message input form       │   • Ticket list + download    │
│                              │   • FAQ knowledge base        │
└──────────────────────────────┬────────────────────────────────┘
                               │
             ┌─────────────────▼─────────────────┐
             │        chatbot_engine.py           │
             │                                   │
             │  1. Guardrail check               │
             │  2. FAQ keyword match             │
             │  3. Intent detection              │
             │  4. Escalation gate               │
             │  5. Sentiment analysis            │
             │  6. Ticket generation             │
             └─────────────────┬─────────────────┘
                               │ (steps 3–4 need LLM)
             ┌─────────────────▼─────────────────┐
             │       watsonx_client.py            │
             │   IBM IAM Token (auto-refresh)     │
             │   Llama 3 multi-turn chat prompt   │
             └─────────────────┬─────────────────┘
                               │ HTTPS
             ┌─────────────────▼─────────────────┐
             │        IBM watsonx.ai              │
             │   meta-llama/llama-3-3-70b-instruct│
             │        Region: au-syd              │
             └───────────────────────────────────┘
```

---

## 🛡️ Responsible AI & Security

| Feature | Implementation |
|---|---|
| **No secret exposure** | All credentials in `.env` (git-ignored), never in source code |
| **Guardrails** | 9 harmful/adversarial topic patterns blocked before LLM call |
| **Prompt injection protection** | `"ignore previous instructions"` and `"jailbreak"` blocked |
| **Human-in-the-loop** | Escalation keywords trigger human agent handoff |
| **Responsible tone** | System prompt enforces empathetic, honest, non-harmful replies |
| **FAQ-first** | Common questions answered from knowledge base — no hallucination risk |

---

## 📺 Application Walkthrough

### Chat Panel
- Type any support question or click a **Quick Reply** chip
- **Aria** responds with intent-aware, context-aware replies
- Escalation keywords (e.g. "speak to an agent") trigger automatic handoff
- Sentiment emoji and intent badge shown on every bot reply

### Live Dashboard
- **Sentiment Trend** — line chart of customer sentiment across all turns
- **Intent Donut** — breakdown of billing / technical / account / general turns
- **Tickets tab** — generated tickets with priority, summary, and JSON download
- **FAQ tab** — browse all 8 FAQ entries

### Generating a Ticket
1. Chat until your issue is explained
2. Click **Generate Summary Ticket** in the sidebar
3. AI summarises the conversation → ticket created with ID, priority, and notes
4. Download as JSON for your CRM

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Meta Llama 3.3 70B Instruct via IBM watsonx.ai |
| **Frontend** | Streamlit 1.35+ with Plotly charts |
| **Auth** | IBM IAM (API Key → Bearer Token, auto-refreshed) |
| **Sentiment** | Lexicon-based (no ML deps) |
| **Tickets** | UUID-based JSON generation |
| **Region** | IBM Cloud Sydney (`au-syd`) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">🤖 AI Customer Support · Powered by IBM watsonx.ai</p>
