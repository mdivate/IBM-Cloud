<div align="center">

# ✍️ Writing Pulse
## Agentic AI Blogging Assistant

[![Python](https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-ff4b4b?logo=streamlit&logoColor=white)](https://streamlit.io)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe?logo=ibm&logoColor=white)](https://www.ibm.com/watsonx)
[![IBM Granite](https://img.shields.io/badge/LLM-IBM%20Granite%203.3-6929c4?logo=ibm&logoColor=white)](https://www.ibm.com/granite)
[![IBM Code Engine](https://img.shields.io/badge/Deploy-IBM%20Code%20Engine-0f62fe?logo=ibm&logoColor=white)](https://cloud.ibm.com/codeengine)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/mdivate/Project-No-5/pulls)

**A fully agentic, multi-agent AI blogging assistant powered by IBM Granite LLM via IBM watsonx.ai.**  
Collect real-time news · suggest trending topics · generate SEO blog drafts · analyze audience sentiment · predict engagement  
— all from an interactive Streamlit dashboard, deployed on **IBM Cloud Code Engine**.

[🚀 Local Quick Start](#-local-quick-start) · [☁️ IBM Cloud Deploy](#️-ibm-cloud-deployment) · [✨ Features](#-features) · [🏗️ Architecture](#️-architecture) · [⚙️ Configuration](#️-configuration)

</div>

---

## ✨ Features

| # | Feature | Description |
|---|---|---|
| 📊 | **Writing Pulse Dashboard** | 5-KPI metrics, live headlines from 10 RSS feeds, trending keyword bar chart, 4-step workflow guide |
| 🔍 | **Research Agent** | Fetches articles from 10 RSS feeds; IBM Granite synthesizes a 280–350-word summary with numbered source citations `[1][2]` |
| 📈 | **Trend Analysis Agent** | Real-time keyword frequency with feed-source attribution; AI-generated SEO topics with differentiating angles |
| ✏️ | **Content Generation Agent** | Full SEO drafts — focus keyword, meta description, H2/H3 structure, CTA; accepts **text + image + voice (.wav)** |
| 🎯 | **Editorial Review Agent** | Readability / SEO Quality / Engagement score gauges (0–10); strengths, improvements, fact-check flags |
| 🧑 | **Human-in-the-Loop Gate** | ✅ Approve / ❌ Revise decision gate — AI recommends, humans decide |
| 💬 | **Audience Sentiment** | Negation- and intensity-aware lexicon; per-comment emoji breakdown; donut chart |
| 📱 | **Social Media Generator** | Twitter/X (≤280 chars), LinkedIn, Instagram; engagement score, reach, optimal publish window |
| 🛡️ | **Responsible AI Guardrails** | 17-category input **and** output content filter; citations; fact-check flags |
| 🔄 | **Model Fallback** | Granite → Llama 3.3 70B transparent failover — zero downtime |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│               Streamlit Web UI  ·  app.py  (8 pages)             │
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
                               │  HTTPS
                    ┌──────────▼───────────┐
                    │   IBM watsonx.ai     │
                    │   Region: au-syd     │
                    │   IBM Granite 3.3 8B │◄── primary
                    │   Llama 3.3 70B      │◄── fallback
                    └──────────────────────┘
```

---

## 🗂️ Project Structure

```
Project-No-5/
│
├── app.py                      # Streamlit dashboard — 8 interactive pages
├── config.py                   # Centralised config — secrets from env vars only
├── watsonx_client.py           # IBM watsonx.ai client (Granite + Llama fallback)
├── requirements.txt            # Pinned production dependencies
├── Dockerfile                  # Production container (IBM Cloud Code Engine)
├── deploy.sh                   # Linux/macOS deployment script
├── deploy.ps1                  # Windows PowerShell deployment script
├── .env.example                # Environment template — copy to .env
├── .gitignore                  # Excludes .env, caches, venvs
├── .dockerignore               # Excludes secrets & dev files from image
│
├── .streamlit/
│   └── config.toml             # Streamlit production settings (port 8080)
│
└── agents/
    ├── __init__.py
    ├── research_agent.py        # RSS fetch + AI synthesis + APA citations
    ├── trend_agent.py           # Keyword trends + topic suggestions + engagement
    ├── content_agent.py         # Blog draft + social snippets + guardrails
    └── editorial_agent.py       # Editorial review + sentiment + approval gate
```

---

## 🚀 Local Quick Start

### 1. Clone

```bash
git clone https://github.com/mdivate/Project-No-5.git
cd Project-No-5
```

### 2. Virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121
WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
```

### 5. Run

```bash
streamlit run app.py
```

Open **[http://localhost:8501](http://localhost:8501)**

---

## ☁️ IBM Cloud Deployment

The application is packaged as a Docker container and deployed to **IBM Cloud Code Engine** — IBM's fully managed serverless container platform. It auto-scales from 1 to 3 instances and exposes a public HTTPS URL.

### Prerequisites

| Tool | Install |
|---|---|
| IBM Cloud CLI | `winget install IBM.IBMCloudCLI` (Windows) or [Download](https://cloud.ibm.com/docs/cli) |
| Code Engine plugin | `ibmcloud plugin install code-engine` |
| Container Registry plugin | `ibmcloud plugin install container-registry` |
| Docker Desktop | [Download](https://www.docker.com/products/docker-desktop/) |

### Step-by-Step Deployment

#### Step 1 — Install IBM Cloud CLI plugins

```bash
ibmcloud plugin install code-engine
ibmcloud plugin install container-registry
ibmcloud plugin list
```

#### Step 2 — Login to IBM Cloud

```bash
ibmcloud login --apikey YOUR_IBM_API_KEY -r au-syd -g Default
```

#### Step 3 — Create a Code Engine project

```bash
ibmcloud ce project create --name writing-pulse-project
ibmcloud ce project select  --name writing-pulse-project
```

#### Step 4 — Create an IBM Container Registry namespace

```bash
ibmcloud cr login
ibmcloud cr namespace-add writing-pulse-ns
```

#### Step 5 — Build and push the Docker image

```bash
# Build for linux/amd64 (required for Code Engine)
docker build --platform linux/amd64 \
    -t au.icr.io/writing-pulse-ns/writing-pulse:v2.0 .

# Push to IBM Container Registry
docker push au.icr.io/writing-pulse-ns/writing-pulse:v2.0
```

#### Step 6 — Create the Code Engine application

```bash
ibmcloud ce application create \
    --name writing-pulse-app \
    --image au.icr.io/writing-pulse-ns/writing-pulse:v2.0 \
    --port 8080 \
    --cpu 1 \
    --memory 4G \
    --min-scale 1 \
    --max-scale 3 \
    --env WATSONX_API_KEY=your_api_key \
    --env WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121 \
    --env WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com \
    --env WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
```

#### Step 7 — Get your public URL

```bash
ibmcloud ce application get --name writing-pulse-app | grep URL
```

Your app will be live at a URL like:
```
https://writing-pulse-app.xxxxxxxxx.au-syd.codeengine.appdomain.cloud
```

---

### 🖱️ Automated Deployment (Script)

Instead of running each step manually, use the included script:

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy.ps1
```

**Linux / macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

### ♻️ Update an Existing Deployment

After changing code:

```bash
# Rebuild and push
docker build --platform linux/amd64 \
    -t au.icr.io/writing-pulse-ns/writing-pulse:v2.1 .
docker push au.icr.io/writing-pulse-ns/writing-pulse:v2.1

# Update the running app (zero-downtime rolling update)
ibmcloud ce application update \
    --name writing-pulse-app \
    --image au.icr.io/writing-pulse-ns/writing-pulse:v2.1
```

---

### 📊 Monitor & Manage

```bash
# View live logs
ibmcloud ce application logs --name writing-pulse-app --follow

# Check status
ibmcloud ce application get --name writing-pulse-app

# List all revisions
ibmcloud ce application revision list --application writing-pulse-app

# Scale manually
ibmcloud ce application update --name writing-pulse-app --min-scale 2

# Delete (tear down)
ibmcloud ce application delete --name writing-pulse-app
```

---

### 🔐 Secrets Management (Production Best Practice)

Instead of passing secrets as `--env` flags (visible in CLI history), use IBM Code Engine secrets:

```bash
# Create a secret holding all credentials
ibmcloud ce secret create \
    --name watsonx-credentials \
    --from-literal WATSONX_API_KEY=your_key \
    --from-literal WATSONX_PROJECT_ID=280ea383-d47b-42ab-a981-b28f66296121 \
    --from-literal WATSONX_ENDPOINT=https://au-syd.ml.cloud.ibm.com \
    --from-literal WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct

# Reference the secret in the app
ibmcloud ce application update \
    --name writing-pulse-app \
    --env-from-secret watsonx-credentials
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Default |
|---|---|---|---|
| `WATSONX_API_KEY` | ✅ | IBM Cloud API key | — |
| `WATSONX_PROJECT_ID` | ✅ | watsonx.ai Project ID | `280ea383-...` |
| `WATSONX_ENDPOINT` | No | Regional API endpoint | `https://au-syd.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | No | Foundation model | `ibm/granite-3-3-8b-instruct` |

### IBM Cloud Regions

| Region | Endpoint | ICR Registry |
|---|---|---|
| **Sydney ✅** | `https://au-syd.ml.cloud.ibm.com` | `au.icr.io` |
| Dallas | `https://us-south.ml.cloud.ibm.com` | `us.icr.io` |
| Frankfurt | `https://eu-de.ml.cloud.ibm.com` | `de.icr.io` |
| Tokyo | `https://jp-tok.ml.cloud.ibm.com` | `jp.icr.io` |

### Models

| Model ID | Type | Notes |
|---|---|---|
| `ibm/granite-3-3-8b-instruct` | IBM Granite | **Primary** — fast, IBM-native |
| `meta-llama/llama-3-3-70b-instruct` | Llama | **Automatic fallback** |

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **Primary LLM** | IBM Granite 3.3 8B Instruct via IBM watsonx.ai |
| **Fallback LLM** | Meta Llama 3.3 70B Instruct via IBM watsonx.ai |
| **Frontend** | Streamlit 1.45 with Plotly interactive charts |
| **Container** | Docker (python:3.11-slim) |
| **Cloud Platform** | IBM Cloud Code Engine (serverless containers) |
| **Container Registry** | IBM Cloud Container Registry (ICR) |
| **Agents** | Pure Python — no framework overhead |
| **News Feeds** | feedparser — 10 public RSS feeds |
| **Sentiment** | Custom lexicon (negation + intensity-aware, zero ML deps) |
| **Voice Input** | SpeechRecognition + Google Speech API (optional) |
| **IAM Auth** | IBM IAM API Key → Bearer Token (auto-refreshed) |
| **Region** | IBM Cloud Sydney (`au-syd`) |

---

## 🛡️ Responsible AI

| Principle | Implementation |
|---|---|
| **No secret exposure** | Credentials in `.env` / Code Engine secrets — never in source or image |
| **Input guardrails** | 17 harmful content categories blocked **before** LLM call |
| **Output guardrails** | LLM responses scanned **after** generation |
| **Human-in-the-loop** | Manual approval gate — the AI recommends, humans decide |
| **Source citations** | Numbered citations `[1][2]` in every research summary |
| **Fact-check flags** | Editorial agent flags questionable claims explicitly |
| **Model fallback** | Granite → Llama 3.3 70B automatic failover |

---

## 🔌 RSS News Sources (10 Feeds)

TechCrunch · Wired · MIT Technology Review · Hacker News · Dev.to · The Verge · Ars Technica · VentureBeat · InfoQ · ZDNet

---

## 🤝 Contributing

1. Fork the repo
2. `git checkout -b feature/your-feature`
3. `git commit -m 'Add your feature'`
4. `git push origin feature/your-feature`
5. Open a [Pull Request](https://github.com/mdivate/Project-No-5/pulls)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [IBM watsonx.ai](https://www.ibm.com/watsonx) — Foundation model platform
- [IBM Granite](https://www.ibm.com/granite) — Open-source enterprise LLM
- [IBM Code Engine](https://cloud.ibm.com/codeengine) — Serverless container platform
- [Streamlit](https://streamlit.io) — Python web app framework

---

<div align="center">

**✍️ Writing Pulse v2.0**  
Made with ❤️ using IBM watsonx.ai · IBM Granite · IBM Code Engine · Streamlit

</div>
