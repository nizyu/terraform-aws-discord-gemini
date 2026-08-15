"""Gemini API Client

Interacts with Google Gemini REST API v1beta.
Supports multi-turn chat conversations, thinking levels, exponential backoff retries,
and automatic fallback to secondary models (e.g. gemini-3.6-flash).
"""

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.7-flash",
        fallback_model: Optional[str] = "gemini-3.6-flash",
    ):
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model

    def _call_model(
        self,
        model_name: str,
        payload: Dict[str, Any],
        max_retries: int = 2,
    ) -> str:
        """Call Gemini API for a given model with exponential backoff retries."""
        url = f"{GEMINI_API_BASE_URL}/models/{model_name}:generateContent?key={self.api_key}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Discord-Gemini-Bot/1.0",
            },
            method="POST",
        )

        last_error = None
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=60) as res:
                    body = res.read().decode("utf-8")
                    response_json = json.loads(body)

                    candidates = response_json.get("candidates", [])
                    if not candidates:
                        finish_reason = response_json.get("promptFeedback", {}).get("blockReason", "UNKNOWN")
                        raise RuntimeError(f"Gemini returned no candidates (blockReason: {finish_reason})")

                    candidate = candidates[0]
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])
                    return "".join([p.get("text", "") for p in parts])

            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e.fp else ""
                last_error = RuntimeError(f"Gemini API Error ({e.code}) on {model_name}: {error_body}")
                if e.code in (503, 502, 504, 429) and attempt < max_retries - 1:
                    wait_seconds = (2 ** attempt) + 1
                    logger.warning(
                        f"Gemini API returned HTTP {e.code} for {model_name} (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_seconds}s..."
                    )
                    time.sleep(wait_seconds)
                    continue
                logger.error(f"Gemini API HTTPError {e.code} on {model_name}: {error_body}")
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1 and isinstance(e, (TimeoutError, urllib.error.URLError)):
                    wait_seconds = (2 ** attempt) + 1
                    logger.warning(f"Connection error for {model_name} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_seconds}s...")
                    time.sleep(wait_seconds)
                    continue
                logger.error(f"Gemini API error on {model_name}: {e}", exc_info=True)
                break

        if last_error:
            raise last_error
        raise RuntimeError(f"Failed to generate content with {model_name}")

    def generate_response(
        self,
        prompt: str,
        context: List[Dict[str, Any]] = None,
        system_instruction: str = "You are a helpful, friendly, and concise assistant in a family Discord server. Answer in Japanese naturally and politely.",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate response from Gemini API with automatic fallback to secondary model on error."""
        if context is None:
            context = []

        messages = list(context)
        user_turn = {
            "role": "user",
            "parts": [{"text": prompt}],
        }
        messages.append(user_turn)

        payload: Dict[str, Any] = {
            "contents": messages,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
                "thinkingConfig": {
                    "thinkingLevel": "LOW",
                },
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        reply_text = None
        # 1. Try primary model
        try:
            reply_text = self._call_model(self.model, payload, max_retries=2)
        except Exception as primary_err:
            if self.fallback_model and self.fallback_model != self.model:
                logger.warning(
                    f"Primary model '{self.model}' failed ({primary_err}). "
                    f"Attempting fallback to '{self.fallback_model}'..."
                )
                try:
                    reply_text = self._call_model(self.fallback_model, payload, max_retries=2)
                    logger.info(f"Successfully generated response using fallback model '{self.fallback_model}'")
                except Exception as fallback_err:
                    logger.error(f"Fallback model '{self.fallback_model}' also failed: {fallback_err}")
                    raise primary_err
            else:
                raise primary_err

        # Append model turn to context
        model_turn = {
            "role": "model",
            "parts": [{"text": reply_text}],
        }
        messages.append(model_turn)

        return reply_text, messages
