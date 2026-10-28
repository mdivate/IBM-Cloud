# ✍️ Writing Pulse — Agentic AI Blogging Assistant

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-ff4b4b?logo=streamlit)](https://streamlit.io)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe?logo=ibm)](https://www.ibm.com/watsonx)
[![LLM](https://img.shields.io/badge/LLM-Llama%203.3%2070B-orange?logo=meta)](https://ai.meta.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> A fully agentic AI-powered blogging assistant that collects real-time information from news feeds, suggests trending topics, generates SEO-optimised blog drafts, analyzes audience sentiment, and predicts engagement — all powered by **Meta Llama 3.3 70B Instruct** via **IBM watsonx.ai** (Sydney region).

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Writing Pulse Dashboard** | Real-time trending keywords, headlines, and blog status overview |
| 🔍 **Research Agent** | Fetches articles from 7 RSS news feeds, synthesizes AI research summaries with source citations |
| 📈 **Trend Agent** | Extracts trending keywords, suggests 5 SEO blog topics, predicts engagement score (0–100) |
| ✏️ **Content Agent** | Generates full SEO blog drafts from text, image description, or voice input |
| 🎯 **Editorial Agent** | AI reviews draft for readability, SEO, engagement; human approval gate before publish |
| 💬 **Audience Sentiment** | Analyzes comments/feedback with per-comment breakdown and donut chart |
| 📱 **Social Media** | Auto-generates Twitter/X, LinkedIn, Instagram posts from blog content |
| 🛡️ **Responsible AI** | Input/output guardrails, no secret exposure, human-in-the-loop approval |

---

## 🏗️ Project Structure

```
blog_assistant/
├── app.py                      # Streamlit frontend (Writing Pulse UI)
├── config.py                   # Centralised config — secrets from env vars only
├── watsonx_client.py           # IBM watsonx.ai LLM client (IAM token + Llama 3 prompt)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template (safe to commit)
├── .env                        # Your actual secrets (git-ignored)
└── agents/
    ├── __init__.py
    ├── research_agent.py       # RSS feed fetching + AI research summarization
    ├── trend_agent.py          # Keyword extraction, topic suggestions, engagement prediction
    ├── content_agent.py        # Blog draft generation, social snippets, voice transcription
    └── editorial_agent.py      # AI editorial review, sentiment analysis, human approval
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- An IBM Cloud account with **watsonx.ai** access
- IBM watsonx.ai **Project ID** and **API Key**

### 1. Clone the repository

```bash
git clone https://github.com/mdivate/IBM-Cloud.git
cd IBM-Cloud/blog_assistant
```

### 2. Create and activate a virtual environment

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

> **Note on PyAudio (voice input):** PyAudio requires system audio libraries.  
> On Windows: `pip install pipwin && pipwin install pyaudio`  
> On Ubuntu: `sudo apt-get install portaudio19-dev && pip install pyaudio`  
> Voice input is optional — the app works without it.

### 4. Configure environment variables

Copy the example file and fill in your credentials:

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

### 5. Run the application

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## ⚙️ Configuration

| Variable | Description | Default |
|---|---|---|
| `WATSONX_API_KEY` | IBM Cloud API Key | *(required)* |
| `WATSONX_PROJECT_ID` | watsonx.ai Project ID | `280ea383-d47b-42ab-a981-b28f66296121` |
| `WATSONX_ENDPOINT` | watsonx.ai regional endpoint | `https://au-syd.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | Foundation model ID | `meta-llama/llama-3-3-70b-instruct` |

### Supported Regions

| Region | Endpoint |
|---|---|
| **Sydney** ✅ | `https://au-syd.ml.cloud.ibm.com` |
| Dallas | `https://us-south.ml.cloud.ibm.com` |
| Frankfurt | `https://eu-de.ml.cloud.ibm.com` |
| Tokyo | `https://jp-tok.ml.cloud.ibm.com` |

---

## 🧠 Architecture

```
┌────────────────────────────────────────────────────────────┐
│              Streamlit Web UI  (app.py)                    │
│                                                            │
│  Dashboard │ Research │ Write │ Review │ Sentiment │ Social│
└──────┬───────────┬───────────┬──────────┬──────────┬───────┘
       │           │           │          │          │
  ┌────▼───┐  ┌────▼───┐  ┌───▼────┐  ┌──▼────┐  ┌──▼──────┐
  │Research│  │ Trend  │  │Content │  │Editor │  │Sentiment│
  │ Agent  │  │ Agent  │  │ Agent  │  │ Agent │  │ Agent   │
  └────┬───┘  └────┬───┘  └───┬────┘  └──┬────┘  └─────────┘
       └───────────┴───────────┴──────────┘
                         │
                ┌────────▼────────┐
                │ WatsonxClient   │
                │ (IAM + LLM API) │
                └────────┬────────┘
                         │ HTTPS
                ┌────────▼────────┐
                │ IBM watsonx.ai  │
                │ au-syd region   │
                │ Llama 3.3 70B   │
                └─────────────────┘
```

---

## 🛡️ Responsible AI & Security

| Principle | Implementation |
|---|---|
| **No secret exposure** | All credentials in `.env` (git-ignored), never in source code |
| **Input guardrails** | 8 harmful content categories blocked before LLM call |
| **Output guardrails** | LLM responses scanned before display |
| **Human-in-the-loop** | Manual approval gate before blog is marked publishable |
| **Source citations** | Research summaries cite article source numbers [1][2] |
| **Fact-check flags** | Editorial agent flags potentially questionable claims |
| **Responsible tone** | System prompts enforce balanced, objective, non-harmful content |

---

## 📺 Application Walkthrough

### 1. Dashboard
Real-time headlines + trending keyword bar chart. Quick-start guide.

### 2. Research & Trends
- Paste a topic → fetch matching articles from 7 news RSS feeds
- Click **Summarize with AI** → AI synthesizes a cited research summary
- Switch to **Trending Topics** → see keyword frequency chips + AI blog suggestions

### 3. Write Blog
- Set topic, tone, word count
- Optionally add image description or voice note
- AI generates: SEO title, meta description, full structured blog, hashtags

### 4. Editorial Review
- AI scores draft on readability, SEO, engagement (0–10 each)
- Lists strengths, improvements, fact-check flags
- Human approval gate: ✅ Approve or ❌ Send back for revision

### 5. Audience Insights
- Paste comments → lexicon sentiment analysis per comment
- Donut chart + per-comment positive/negative/neutral breakdown

### 6. Social Media
- Auto-generates Twitter/X (≤280 chars), LinkedIn, and Instagram posts
- Predicts best publish day, time, and engagement score

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Meta Llama 3.3 70B Instruct via IBM watsonx.ai |
| **Frontend** | Streamlit 1.35+ with Plotly charts |
| **Agents** | Pure Python (no framework overhead) |
| **News Data** | feedparser + BeautifulSoup4 (7 RSS feeds) |
| **Sentiment** | Lexicon-based (no ML deps required) |
| **Voice Input** | SpeechRecognition + Google Speech API |
| **Auth** | IBM IAM (API Key → Bearer Token, auto-refreshed) |
| **Region** | IBM Cloud Sydney (`au-syd`) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">✍️ Made with IBM watsonx.ai · Writing Pulse Agentic AI</p>
