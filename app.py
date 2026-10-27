"""
Nutrition Agentic AI Application
Powered by Meta Llama 3.3 70B via IBM watsonx.ai (Sydney)
"""

import os
import re
import requests
from flask import Flask, request, jsonify, render_template, session
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # load .env file if present

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# ─── IBM watsonx.ai Configuration ────────────────────────────────────────────
# Set these in a .env file locally or as environment variables in production.
# NEVER hardcode secrets in source code.
IBM_API_KEY    = os.environ.get("IBM_API_KEY", "")
IBM_PROJECT_ID = os.environ.get("IBM_PROJECT_ID", "")
IBM_ENDPOINT   = os.environ.get("IBM_ENDPOINT", "https://au-syd.ml.cloud.ibm.com")
IBM_MODEL_ID   = os.environ.get("IBM_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")
IAM_TOKEN_URL  = "https://iam.cloud.ibm.com/identity/token"

# ─── Token Cache ─────────────────────────────────────────────────────────────
_token_cache = {"token": None, "expires_at": None}


def get_iam_token():
    """Fetch and cache IBM IAM Bearer token."""
    now = datetime.utcnow()
    if _token_cache["token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    resp = requests.post(
        IAM_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": IBM_API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + timedelta(seconds=data.get("expires_in", 3600) - 60)
    return _token_cache["token"]


def call_granite(prompt: str, max_tokens: int = 1024) -> str:
    """Call IBM Granite LLM via watsonx.ai."""
    token = get_iam_token()
    url = f"{IBM_ENDPOINT}/ml/v1/text/generation?version=2025-02-11"

    payload = {
        "model_id": IBM_MODEL_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "sample",
            "max_new_tokens": max_tokens,
            "min_new_tokens": 50,
            "stop_sequences": ["<|eot_id|>"],
            "repetition_penalty": 1.1,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "project_id": IBM_PROJECT_ID,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    return result["results"][0]["generated_text"].strip()


# ─── Guardrails ───────────────────────────────────────────────────────────────
HARMFUL_KEYWORDS = [
    "suicide", "self-harm", "kill yourself", "overdose",
    "illegal drug", "poison", "starve yourself", "eating disorder",
    "extreme fasting", "crash diet", "laxative abuse",
]

MEDICAL_DISCLAIMER = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚕️  MEDICAL DISCLAIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The nutrition information provided by this AI application is for 
general informational and educational purposes only. It is NOT a 
substitute for professional medical advice, diagnosis, or treatment.

Always consult a qualified healthcare provider or registered dietitian 
before making significant changes to your diet, especially if you have 
a pre-existing medical condition such as diabetes, hypertension, or 
cardiovascular disease.

Do not disregard professional medical advice or delay seeking it 
because of something you have read in this application.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def apply_guardrails(text: str) -> bool:
    """Return True if the text is safe, False if harmful content detected."""
    lower = text.lower()
    for kw in HARMFUL_KEYWORDS:
        if kw in lower:
            return False
    return True


def sanitize_input(text: str) -> str:
    """Remove potentially dangerous characters from user input."""
    text = re.sub(r"[<>\"'%;()&+]", "", text)
    return text[:500]  # limit length


# ─── Agent Prompts (Llama 3 chat template) ───────────────────────────────────

def _llama_prompt(system: str, user_msg: str) -> str:
    """Wrap system + user message in the Llama 3 chat template."""
    return (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n\n"
        f"{system.strip()}"
        "<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg.strip()}"
        "<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
    )


def build_nutrition_prompt(user: dict) -> str:
    medical = user.get("medical_history", "None reported")
    system = (
        "You are NutriGuide, a professional, compassionate, and ethical AI nutrition assistant. "
        "You provide safe, practical, evidence-based dietary advice. "
        "You never recommend extreme diets, crash diets, or anything harmful. "
        "Always use a helpful, respectful, and encouraging tone."
    )
    user_msg = f"""Please create a detailed personalized daily nutrition plan for:
- Name: {user['name']}
- Age: {user['age']}
- Diet Preference: {user['diet']}
- Medical History: {medical}
- Location: {user['city']}, {user['country']}

Include these sections:
1. Daily Calorie Target (with justification)
2. Macronutrient Breakdown (Carbohydrates, Protein, Fat)
3. Recommended Foods (locally available in {user['city']}, {user['country']})
4. Foods to Avoid (based on medical history)
5. Sample Meal Plan (Breakfast, Lunch, Dinner, Snacks)
6. Hydration Recommendation
7. Supplement Suggestions (if appropriate)
8. Lifestyle Tips

Rules:
- Strictly respect the {user['diet']} dietary preference.
- If diabetes is mentioned, recommend low-glycemic foods.
- If blood pressure is mentioned, recommend low-sodium foods.
- Keep advice practical and achievable."""
    return _llama_prompt(system, user_msg)


def build_query_prompt(user_profile: dict, query: str) -> str:
    name = user_profile.get("name", "User") if user_profile else "User"
    diet = user_profile.get("diet", "not specified") if user_profile else "not specified"
    medical = user_profile.get("medical_history", "None") if user_profile else "None"

    system = (
        "You are NutriGuide, a knowledgeable, ethical, and empathetic AI nutrition assistant. "
        "Answer questions about nutrition, diet, and wellness helpfully and accurately. "
        "If a question involves a medical condition, recommend consulting a healthcare provider. "
        "Do not provide harmful, dangerous, or unethical advice. "
        "If a question is unrelated to nutrition or health, politely redirect."
    )
    user_msg = f"""User profile: Name={name}, Diet={diet}, Medical History={medical}

Question: {query}"""
    return _llama_prompt(system, user_msg)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/api/generate-plan", methods=["POST"])
def generate_plan():
    try:
        data = request.get_json()

        # Sanitize inputs
        user = {
            "name": sanitize_input(data.get("name", "User")),
            "age": sanitize_input(str(data.get("age", "30"))),
            "diet": sanitize_input(data.get("diet", "vegetarian")),
            "medical_history": sanitize_input(data.get("medical_history", "None")),
            "city": sanitize_input(data.get("city", "Unknown")),
            "country": sanitize_input(data.get("country", "Unknown")),
        }

        # Guardrail check on inputs
        combined_input = " ".join(user.values())
        if not apply_guardrails(combined_input):
            return jsonify({
                "success": False,
                "error": "Your input contains content that cannot be processed. Please keep queries health-focused."
            }), 400

        # Store user profile in session
        session["user_profile"] = user

        # Build and call LLM
        prompt = build_nutrition_prompt(user)
        response = call_granite(prompt, max_tokens=1200)

        # Guardrail check on output
        if not apply_guardrails(response):
            response = ("I'm sorry, I was unable to generate a safe nutrition plan with the provided information. "
                        "Please consult a registered dietitian for personalized advice.")

        return jsonify({
            "success": True,
            "plan": response,
            "disclaimer": MEDICAL_DISCLAIMER,
            "user": user,
        })

    except requests.exceptions.HTTPError as e:
        return jsonify({"success": False, "error": f"IBM watsonx API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        query = sanitize_input(data.get("message", ""))

        if not query:
            return jsonify({"success": False, "error": "Empty message."}), 400

        # Guardrail check
        if not apply_guardrails(query):
            return jsonify({
                "success": True,
                "response": ("I'm sorry, I can't assist with that request. "
                             "Please ask health and nutrition-related questions. "
                             "If you're going through a difficult time, please reach out to a healthcare professional.")
            })

        # Get user profile from session if available
        user_profile = session.get("user_profile", {})

        prompt = build_query_prompt(user_profile, query)
        response = call_granite(prompt, max_tokens=512)

        # Guardrail on output
        if not apply_guardrails(response):
            response = ("I'm unable to provide that information. Please consult a qualified healthcare professional.")

        return jsonify({"success": True, "response": response})

    except requests.exceptions.HTTPError as e:
        return jsonify({"success": False, "error": f"IBM watsonx API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "model": IBM_MODEL_ID, "timestamp": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
