"""
watsonx_client.py — IBM watsonx.ai LLM client with IAM token caching.
Uses meta-llama/llama-3-3-70b-instruct (confirmed live in au-syd).
"""

import requests
from datetime import datetime, timedelta
from config import Config


class WatsonxClient:
    """Thread-safe IBM watsonx.ai client with automatic IAM token refresh."""

    def __init__(self):
        self._token: str = ""
        self._expires_at: datetime = datetime.utcnow()

    # ── IAM auth ──────────────────────────────────────────────────────────────

    def _refresh_token(self) -> str:
        if self._token and datetime.utcnow() < self._expires_at:
            return self._token
        if not Config.WATSONX_API_KEY:
            raise ValueError(
                "WATSONX_API_KEY is not set. Add it to your .env file or environment."
            )
        resp = requests.post(
            Config.IAM_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": Config.WATSONX_API_KEY,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = datetime.utcnow() + timedelta(
            seconds=data.get("expires_in", 3600) - 120
        )
        return self._token

    # ── Core generation ───────────────────────────────────────────────────────

    def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.7) -> str:
        """
        Call the LLM with a pre-formatted Llama 3 chat prompt.
        Returns the generated text string.
        """
        token = self._refresh_token()
        url = (
            f"{Config.WATSONX_ENDPOINT}/ml/v1/text/generation"
            f"?version={Config.WATSONX_API_VER}"
        )
        payload = {
            "model_id": Config.WATSONX_MODEL_ID,
            "input": prompt,
            "parameters": {
                "decoding_method": "sample",
                "max_new_tokens": max_tokens or Config.DEFAULT_MAX_TOKENS,
                "min_new_tokens": 30,
                "temperature": temperature,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
                "stop_sequences": ["<|eot_id|>"],
            },
            "project_id": Config.WATSONX_PROJECT_ID,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["results"][0]["generated_text"].strip()

    # ── Prompt builder (Llama 3 chat template) ────────────────────────────────

    @staticmethod
    def build_prompt(system: str, user_msg: str) -> str:
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

    def ask(self, system: str, user_msg: str, max_tokens: int = None, temperature: float = 0.7) -> str:
        """Convenience: build Llama 3 prompt and call generate."""
        prompt = self.build_prompt(system, user_msg)
        return self.generate(prompt, max_tokens=max_tokens, temperature=temperature)


# Shared singleton
llm = WatsonxClient()
