"""
watsonx_client.py — IBM watsonx.ai LLM client.
Supports IBM Granite models with automatic IAM token caching and
transparent fallback from Granite to Llama 3.3 70B on model errors.

Prompt strategy:
  • IBM Granite 3.x → chat messages API  (preferred)
  • Llama 3.3 70B   → Llama-3 chat template (fallback)
"""

import json
import requests
from datetime import datetime, timedelta
from config import Config


class WatsonxClient:
    """
    IBM watsonx.ai client with:
    - Automatic IAM Bearer-token refresh (5-min safety buffer)
    - IBM Granite chat-messages API
    - Llama 3 prompt-template fallback
    - Transparent model failover
    """

    def __init__(self):
        self._token: str = ""
        self._expires_at: datetime = datetime.utcnow()
        self._active_model: str = Config.WATSONX_MODEL_ID

    # ── IAM authentication ────────────────────────────────────────────────────

    def _refresh_token(self) -> str:
        """Return cached token or fetch a new one from IBM IAM."""
        if self._token and datetime.utcnow() < self._expires_at:
            return self._token
        if not Config.WATSONX_API_KEY:
            raise ValueError(
                "WATSONX_API_KEY is not set. "
                "Add it to your .env file and restart the application."
            )
        resp = requests.post(
            Config.IAM_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey":     Config.WATSONX_API_KEY,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token      = data["access_token"]
        self._expires_at = datetime.utcnow() + timedelta(
            seconds=data.get("expires_in", 3600) - 300
        )
        return self._token

    # ── IBM Granite — chat/messages endpoint ─────────────────────────────────

    def _call_granite(
        self, system: str, user_msg: str,
        max_tokens: int, temperature: float,
        model_id: str,
    ) -> str:
        """Call the watsonx.ai chat/text/chat endpoint for Granite models."""
        token = self._refresh_token()
        url = (
            f"{Config.WATSONX_ENDPOINT}/ml/v1/text/chat"
            f"?version={Config.WATSONX_API_VER}"
        )
        payload = {
            "model_id":   model_id,
            "project_id": Config.WATSONX_PROJECT_ID,
            "messages": [
                {"role": "system",    "content": system.strip()},
                {"role": "user",      "content": user_msg.strip()},
            ],
            "parameters": {
                "max_new_tokens":   max_tokens,
                "min_new_tokens":   20,
                "temperature":      temperature,
                "top_p":            0.9,
                "repetition_penalty": 1.05,
            },
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # Granite chat response shape: choices[0].message.content
        choices = data.get("choices") or []
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        # Fallback to results[] shape (some watsonx versions)
        results = data.get("results") or []
        if results:
            return results[0].get("generated_text", "").strip()
        return ""

    # ── Llama 3 — text/generation endpoint ───────────────────────────────────

    @staticmethod
    def _llama3_prompt(system: str, user_msg: str) -> str:
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

    def _call_llama(
        self, system: str, user_msg: str,
        max_tokens: int, temperature: float,
        model_id: str,
    ) -> str:
        """Call the watsonx.ai text/generation endpoint for Llama models."""
        token = self._refresh_token()
        url = (
            f"{Config.WATSONX_ENDPOINT}/ml/v1/text/generation"
            f"?version={Config.WATSONX_API_VER}"
        )
        payload = {
            "model_id":   model_id,
            "project_id": Config.WATSONX_PROJECT_ID,
            "input":      self._llama3_prompt(system, user_msg),
            "parameters": {
                "decoding_method":    "sample",
                "max_new_tokens":     max_tokens,
                "min_new_tokens":     20,
                "temperature":        temperature,
                "top_p":              0.9,
                "repetition_penalty": 1.1,
                "stop_sequences":     ["<|eot_id|>"],
            },
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["results"][0]["generated_text"].strip()

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(
        self,
        system: str,
        user_msg: str,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a system+user message to the active Granite model.
        On HTTP/model error, transparently retries with the Llama fallback.
        """
        mt = max_tokens or Config.DEFAULT_MAX_TOKENS
        # Try Granite (chat endpoint) first
        try:
            text = self._call_granite(
                system, user_msg, mt, temperature, self._active_model
            )
            self._active_model = Config.WATSONX_MODEL_ID  # reset on success
            return text
        except Exception:
            pass  # fall through to Llama fallback

        # Llama 3.3 fallback (text/generation)
        self._active_model = Config.WATSONX_FALLBACK_MODEL
        return self._call_llama(
            system, user_msg, mt, temperature, self._active_model
        )

    @property
    def active_model(self) -> str:
        return self._active_model


# ── Module-level singleton ─────────────────────────────────────────────────────
llm = WatsonxClient()
