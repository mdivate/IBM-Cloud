# 🥗 NutriGuide AI — Personalized Nutrition Agentic AI

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-black?logo=flask)](https://flask.palletsprojects.com)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-0f62fe?logo=ibm)](https://www.ibm.com/watsonx)
[![LLM](https://img.shields.io/badge/LLM-Llama%203.3%2070B-orange?logo=meta)](https://ai.meta.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> A **web-based Agentic AI Nutrition Application** powered by **Meta Llama 3.3 70B Instruct** via **IBM watsonx.ai** (Sydney region).  
> Collects user health details and generates a fully personalised nutrition plan — with an integrated AI chat assistant for follow-up queries.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Agentic AI Plan Generation** | Generates a full personalised nutrition plan from user profile (name, age, diet, medical history, location) |
| 💬 **AI Chat Assistant** | Ask any nutrition or wellness question — context-aware using your profile |
| 🛡️ **AI Guardrails** | Input & output safety filtering — blocks harmful content before & after LLM call |
| 🌍 **Location-Aware** | Recommends locally available foods based on city & country |
| ⚕️ **Medical Condition Aware** | Diabetes → low-GI diet; Hypertension → low-sodium diet |
| ❤️ **HAM Tone** | Helpful, Accurate, and Mindful responses throughout |
| ⚕️ **Medical Disclaimer** | Always displayed with every generated nutrition plan |

---

## 🏗️ Project Structure

```
IBM-Cloud/
├── nutrition_ai/
│   ├── app.py                  # Flask backend + IBM watsonx.ai LLM integration
│   ├── requirements.txt        # Python dependencies
│   ├── README.md               # This file
│   └── templates/
│       └── index.html          # Single-page web frontend
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- An IBM Cloud account with watsonx.ai access
- IBM watsonx.ai Project ID & API Key

### 1. Clone the repository

```bash
git clone https://github.com/mdivate/IBM-Cloud.git
cd IBM-Cloud/nutrition_ai
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

### 4. Configure environment variables

Create a `.env` file in the `nutrition_ai/` directory (never commit this file):

```env
IBM_API_KEY=your_ibm_api_key_here
IBM_PROJECT_ID=your_project_id_here
IBM_ENDPOINT=https://au-syd.ml.cloud.ibm.com
```

Or set them directly in your shell:

```bash
# Windows PowerShell
$env:IBM_API_KEY="your_ibm_api_key_here"
$env:IBM_PROJECT_ID="your_project_id_here"

# macOS / Linux
export IBM_API_KEY="your_ibm_api_key_here"
export IBM_PROJECT_ID="your_project_id_here"
```

### 5. Run the application

```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## ⚙️ Configuration

| Variable | Description | Default |
|---|---|---|
| `IBM_API_KEY` | IBM Cloud API Key | *(required)* |
| `IBM_PROJECT_ID` | watsonx.ai Project ID | *(required)* |
| `IBM_ENDPOINT` | watsonx.ai regional endpoint | `https://au-syd.ml.cloud.ibm.com` |
| `IBM_MODEL_ID` | Foundation model ID | `meta-llama/llama-3-3-70b-instruct` |

### Supported IBM watsonx.ai Regions

| Region | Endpoint |
|---|---|
| Sydney | `https://au-syd.ml.cloud.ibm.com` |
| Dallas | `https://us-south.ml.cloud.ibm.com` |
| Frankfurt | `https://eu-de.ml.cloud.ibm.com` |
| Tokyo | `https://jp-tok.ml.cloud.ibm.com` |
| London | `https://eu-gb.ml.cloud.ibm.com` |

---

## 🧠 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Web Browser (User)                    │
│          HTML + CSS + Vanilla JavaScript                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (REST)
┌──────────────────────▼──────────────────────────────────┐
│                Flask Backend (app.py)                   │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Guardrails │  │ Prompt Build │  │ Session Store │  │
│  │  (input +   │  │ (Llama 3     │  │ (user profile │  │
│  │   output)   │  │  template)   │  │  context)     │  │
│  └──────┬──────┘  └──────┬───────┘  └───────────────┘  │
│         └────────────────▼                              │
│                  IBM IAM Token                          │
│                  (auto-refresh)                         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│             IBM watsonx.ai (au-syd)                     │
│       meta-llama/llama-3-3-70b-instruct                 │
└─────────────────────────────────────────────────────────┘
```

### API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serve the web application |
| `POST` | `/api/generate-plan` | Generate personalised nutrition plan |
| `POST` | `/api/chat` | Chat with NutriGuide AI assistant |
| `GET` | `/api/health` | Health check (model + status) |

---

## 🛡️ AI Ethics & Safety

This application follows responsible AI principles:

- **Input Guardrails** — 14 harmful keyword patterns blocked before reaching the LLM
- **Output Guardrails** — LLM response validated for unsafe content before delivery
- **Input Sanitisation** — Special characters stripped; input capped at 500 characters
- **No Extreme Advice** — Prompts explicitly prohibit crash diets, extreme fasting, laxative abuse
- **Medical Condition Handling** — Safe, condition-appropriate recommendations built into prompts
- **Medical Disclaimer** — Shown on every generated plan; users directed to consult professionals
- **HAM Tone** — All prompts engineered for Helpful, Accurate, Mindful responses

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Meta Llama 3.3 70B Instruct via IBM watsonx.ai |
| **Backend** | Python 3.9+, Flask 2.3+ |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Auth** | IBM IAM (API Key → Bearer Token, auto-refreshed) |
| **Region** | IBM Cloud Sydney (`au-syd`) |

---

## ⚕️ Medical Disclaimer

> This application is for **educational and informational purposes only**.  
> It is **NOT** a substitute for professional medical advice, diagnosis, or treatment.  
> Always consult a qualified healthcare provider or registered dietitian before  
> making significant changes to your diet, especially if you have a pre-existing  
> medical condition such as diabetes, hypertension, or cardiovascular disease.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Made with ❤️ using IBM watsonx.ai</p>
