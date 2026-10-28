<div align="center">

# ✍️ Writing Pulse
## Agentic AI Blogging Assistant

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776ab?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-ff4b4b?logo=streamlit&logoColor=white)](https://streamlit.io)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe?logo=ibm&logoColor=white)](https://www.ibm.com/watsonx)
[![IBM Granite](https://img.shields.io/badge/LLM-IBM%20Granite%203.3-6929c4?logo=ibm&logoColor=white)](https://www.ibm.com/granite)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/mdivate/Project-No-5/pulls)

**A fully agentic, multi-agent AI blogging assistant powered by IBM Granite LLM via IBM watsonx.ai.**  
Collect real-time news, suggest trending topics, generate SEO blog drafts, analyze audience sentiment,  
and predict engagement — all from an interactive Streamlit dashboard.

[🚀 Quick Start](#-quick-start) · [✨ Features](#-features) · [🏗️ Architecture](#️-architecture) · [📺 Screenshots](#-app-walkthrough) · [⚙️ Configuration](#️-configuration)

</div>

---

## ✨ Features

| # | Feature | Description |
|---|---|---|
| 📊 | **Writing Pulse Dashboard** | 5-KPI metrics, live headlines from 10 RSS feeds, trending keyword bar chart, 4-step workflow guide |
| 🔍 | **Research Agent** | Fetches articles from 10 public RSS news feeds; IBM Granite synthesizes a 280–350 word summary with numbered source citations `[1][2]` |
| 📈 | **Trend Analysis Agent** | Real-time keyword frequency analysis with feed-source attribution; AI-generated SEO blog topics with differentiating angles |
| ✏️ | **Content Generation Agent** | Full SEO blog drafts — focus keyword, meta description, H2/H3 structure, CTA; accepts **text + image description + voice input (.wav)** |
| 🎯 | **Editorial Review Agent** | Readability / SEO Quality / Engagement score gauges (0–10 each); strengths, improvements, fact-check flags, SEO recommendations |
| 🧑 | **Human-in-the-Loop Gate** | Manual ✅ Approve / ❌ Revise decision gate before publishing — AI recommends, humans decide |
| 💬 | **Audience Sentiment Analysis** | Negation- and intensity-aware lexicon sentiment; per-comment emoji breakdown; donut chart |
| 📱 | **Social Media Generator** | Twitter/X (≤280 chars), LinkedIn, Instagram posts; engagement score, reach level, optimal publish window |
| 🛡️ | **Responsible AI Guardrails** | 17-category input **and** output content filter; no secrets in source code; source citations; fact-check flags |
| 🔄 | **Automatic Model Fallback** | Granite → Llama 3.3 70B transparent failover — zero downtime |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               Streamlit Web UI  ·  app.py  (8 pages)             │
│                                                                    │
│  Dashboard │ Research │ Trends │ Write │ Review │ Audience │ … │
└──────┬───────────┬───────────┬──────────┬──────────┬─────────────┘
       │           │           │          │          │
  ┌────▼────┐ ┌────▼────┐ ┌───▼─────┐ ┌──▼──────┐ ┌▼──────────┐
  │Research │ │ Trend   │ │ Content │ │Editorial│ │ Sentiment │
  │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │ │  (local)  │
  └────┬────┘ └────┬────┘ └───┬─────┘ └──┬──────┘ └───────────┘
       └───────────┴───────────┴──────────┘
                               │
                    ┌──────────▼───────────┐
                    │    WatsonxClient     │
                    │  IAM token refresh   │
                    │  Granite chat API    │
                    │  Llama fallback API  │
                    └──────────┬───────────┘
                               │  HTTPS / REST
                    ┌──────────▼───────────┐
                    │   IBM watsonx.ai     │
                    │   Region: au-syd     │
                    │   IBM Granite 3.3 8B │◄── primary
                    │   Llama 3.3 70B      │◄── fallback
                    └──────────────────────┘
```

### Agent Responsibilities

| Agent | File | Responsibilities |
|---|---|---|
| Research Agent | [`agents/research_agent.py`](agents/research_agent.py) | RSS fetching (10 feeds), multi-word topic matching, AI research synthesis, APA citations |
| Trend Agent | [`agents/trend_agent.py`](agents/trend_agent.py) | Keyword frequency ranking, feed-source attribution, AI blog topic suggestions, engagement prediction |
| Content Agent | [`agents/content_agent.py`](agents/content_agent.py) | Input/output guardrails, SEO draft generation, social post generation, voice transcription |
| Editorial Agent | [`agents/editorial_agent.py`](agents/editorial_agent.py) | AI editorial review, negation-aware sentiment analysis, human approval gate |

---

## 🗂️ Project Structure

```
Project-No-5/
│
├── app.py                    # Streamlit dashboard — 8 interactive pages
├── config.py                 # Centralised configuration (env vars only, no secrets)
├── watsonx_client.py         # IBM watsonx.ai LLM client (Granite + Llama fallback)
├── requirements.txt          # Python dependencies (11 packages)
├── .env.example              # Environment template — copy to .env and fill in
├── .gitignore                # Comprehensive gitignore (secrets, cache, venvs)
│
└── agents/
    ├── __init__.py
    ├── research_agent.py     # Real-time RSS research + AI synthesis + citations
    ├── trend_agent.py        # Keyword trends + AI topic suggestions + engagement
    ├── content_agent.py      # Blog draft + social snippets + voice input + guardrails
    └── editorial_agent.py    # Editorial review + sentiment analysis + approval gate
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **IBM Cloud account** with [watsonx.ai](https://www.ibm.com/watsonx) access
- IBM watsonx.ai **Project ID** and **API Key**
- Git

### 1. Clone the repository

```bash
git clone https://github.com/mdivate/Project-No-5.git
cd Project-No-5
```

### 2. Create a virtual environment (recommended)

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

> **Voice input is optional.** The app works fully without it.
> If you want voice-to-text support, install PyAudio separately:
> - **Windows:** `pip install pipwin && pipwin install pyaudio`
> - **Ubuntu/Debian:** `sudo apt-get install portaudio19-dev && pip install pyaudio`
> - **macOS:** `brew install portaudio && pip install pyaudio`

### 4. Configure your IBM credentials

```bash
cp .env.example .env
```

Open `.env` and set your credentials:

```env
# Your IBM Cloud API Key
WATSONX_API_KEY=your_ibm_cloud_api_key_here

# IBM watsonx.ai Project ID
WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121

# Regional endpoint
WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com

# Primary LLM (IBM Granite — falls back to Llama 3.3 70B automatically)
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
```

> ⚠️ **Never commit your `.env` file.** It is git-ignored by default.

### 5. Launch the application

```bash
streamlit run app.py
```

Open your browser at **[http://localhost:8501](http://localhost:8501)** 🎉

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Default |
|---|---|---|---|
| `WATSONX_API_KEY` | ✅ Yes | IBM Cloud API key | — |
| `WATSONX_PROJECT_ID` | ✅ Yes | watsonx.ai Project ID | `280ea383-...` |
| `WATSONX_ENDPOINT` | No | Regional API endpoint | `https://au-syd.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | No | Foundation model ID | `ibm/granite-3-3-8b-instruct` |

### Supported IBM Cloud Regions

| Region | Endpoint URL |
|---|---|
| **Sydney ✅** | `https://au-syd.ml.cloud.ibm.com` |
| Dallas | `https://us-south.ml.cloud.ibm.com` |
| Frankfurt | `https://eu-de.ml.cloud.ibm.com` |
| Tokyo | `https://jp-tok.ml.cloud.ibm.com` |

### Supported Models

| Model ID | Type | Notes |
|---|---|---|
| `ibm/granite-3-3-8b-instruct` | IBM Granite | **Primary** — fastest, IBM-native |
| `ibm/granite-13b-instruct-v2` | IBM Granite | Alternative Granite option |
| `meta-llama/llama-3-3-70b-instruct` | Llama | **Automatic fallback** |

---

## 📺 App Walkthrough

### 📊 Page 1 — Dashboard
- 5 live KPI metrics: Trending Topics · Articles Found · Draft Status · Review Score · Approval
- **Fetch Live Headlines** → latest news from 10 RSS feeds
- **Refresh Trends** → trending keyword bar chart
- 4-step quick-start workflow guide

### 🔍 Page 2 — Research Agent
- Enter any topic → searches 10 RSS feeds using multi-word matching
- **AI Synthesize** → IBM Granite produces a cited research summary
- Expandable APA-style reference list for every article used

### 📈 Page 3 — Trend Analysis Agent
- Live keyword frequency chips with feed-source attribution
- Interactive horizontal bar chart
- **Suggest Blog Topics** → 5 AI-generated topics, each with:
  - SEO-optimised headline, audience persona, differentiating angle, hashtags
  - One-click **"Use this topic →"** to pre-fill the Write Blog page

### ✏️ Page 4 — Content Generation Agent
- Configure: topic, tone (8 options), word count (300–2,500)
- Multi-modal inputs: text notes · image description · voice transcript (.wav)
- IBM Granite generates: SEO title · focus keyword · meta description · H2/H3 blog structure · CTA
- Inline engagement prediction (score/100, best day/time, reach, hashtags)
- Download as Markdown with citations appended

### 🎯 Page 5 — Editorial Review Agent
- Readability · SEO Quality · Engagement score gauges (0–10 each, colour-coded)
- AI feedback: strengths · improvements needed · fact-check flags · SEO recommendations
- **Human Approval Gate** — ✅ Approve for Publishing or ❌ Send Back for Revision

### 💬 Page 6 — Audience Insights
- Paste any comments, reviews, or feedback (one per line)
- Negation-aware sentiment analysis (`"not bad"` → Positive)
- Intensity weighting (`"absolutely amazing"` > `"good"`)
- Donut chart + per-comment colour-coded breakdown cards

### 📱 Page 7 — Social Media
- Auto-generates Twitter/X (≤280 chars, validated), LinkedIn, Instagram posts
- One-click copy / download for each platform
- Engagement prediction: score/100 · reach level · content type · publish window · hashtags

### ⚙️ Page 8 — Settings
- Config viewer (no secrets shown)
- Guardrail categories list
- All 10 RSS feeds with links
- Publish window scoring reference table

---

## 🛡️ Responsible AI

| Principle | Implementation |
|---|---|
| **No secret exposure** | All credentials in `.env` (git-ignored); never in source code or UI |
| **Input guardrails** | 17 harmful content categories blocked **before** LLM call |
| **Output guardrails** | LLM responses scanned **after** generation |
| **Human-in-the-loop** | Manual approval gate — the AI recommends but humans decide |
| **Source citations** | Every research summary includes numbered citations `[1][2]` |
| **Fact-check flags** | Editorial agent explicitly flags potentially questionable claims |
| **Model fallback** | Automatic Granite → Llama 3.3 70B failover for availability |
| **Responsible prompting** | System prompts enforce factual, balanced, non-harmful content |

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **Primary LLM** | IBM Granite 3.3 8B Instruct via IBM watsonx.ai |
| **Fallback LLM** | Meta Llama 3.3 70B Instruct via IBM watsonx.ai |
| **Frontend** | Streamlit 1.35+ with Plotly interactive charts |
| **Agents** | Pure Python — no agent framework overhead |
| **News Feeds** | feedparser — 10 public RSS feeds |
| **HTML Parsing** | BeautifulSoup4 + lxml |
| **Sentiment** | Custom lexicon (negation + intensity-aware, zero ML deps) |
| **Voice Input** | SpeechRecognition + Google Speech API (optional) |
| **Image Input** | Pillow — image preview + author-described context |
| **IAM Auth** | IBM IAM API Key → Bearer Token (auto-refreshed, 5-min buffer) |
| **Region** | IBM Cloud Sydney (`au-syd`) |

---

## 🔌 RSS News Sources

The application aggregates content from 10 live RSS feeds:

| Source | Feed |
|---|---|
| TechCrunch | `https://techcrunch.com/feed/` |
| Wired | `https://www.wired.com/feed/rss` |
| MIT Technology Review | `https://www.technologyreview.com/feed/` |
| Hacker News Top | `https://hnrss.org/frontpage` |
| Dev.to | `https://dev.to/feed` |
| The Verge | `https://www.theverge.com/rss/index.xml` |
| Ars Technica | `https://feeds.arstechnica.com/arstechnica/index` |
| VentureBeat | `https://venturebeat.com/feed/` |
| InfoQ | `https://www.infoq.com/feed/` |
| ZDNet | `https://www.zdnet.com/news/rss.xml` |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a [Pull Request](https://github.com/mdivate/Project-No-5/pulls)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [IBM watsonx.ai](https://www.ibm.com/watsonx) — Foundation model platform
- [IBM Granite](https://www.ibm.com/granite) — Open-source enterprise LLM
- [Streamlit](https://streamlit.io) — Python web app framework
- [feedparser](https://feedparser.readthedocs.io) — RSS/Atom feed parsing

---

<div align="center">

**✍️ Writing Pulse v2.0**  
Made with ❤️ using IBM watsonx.ai · IBM Granite · Python · Streamlit

</div>
