"""Gemini API Client

Interacts with Google Gemini REST API v1beta.
Supports multi-turn chat conversations using context history.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate_response(
        self,
        prompt: str,
        context: List[Dict[str, Any]] = None,
        system_instruction: str = "You are a helpful, friendly, and concise assistant in a family Discord server. Answer in Japanese naturally and politely.",
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate response from Gemini API given a new prompt and existing conversation context.

        Args:
            prompt: User's input text.
            context: List of previous conversation turns in Gemini format:
                     [{"role": "user", "parts": [{"text": "..."}]}, {"role": "model", "parts": [{"text": "..."}]}]
            system_instruction: Optional system instruction.

        Returns:
            Tuple of (response_text, updated_context_list)
        """
        if context is None:
            context = []

        # Prepare messages
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
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        url = f"{GEMINI_API_BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                body = res.read().decode("utf-8")
                response_json = json.loads(body)

                # Extract text
                candidates = response_json.get("candidates", [])
                if not candidates:
                    finish_reason = response_json.get("promptFeedback", {}).get("blockReason", "UNKNOWN")
                    raise RuntimeError(f"Gemini returned no candidates (blockReason: {finish_reason})")

                candidate = candidates[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])

                reply_text = "".join([p.get("text", "") for p in parts])

                # Append model turn to context
                model_turn = {
                    "role": "model",
                    "parts": [{"text": reply_text}],
                }
                messages.append(model_turn)

                return reply_text, messages

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"Gemini API HTTPError {e.code}: {error_body}")
            raise RuntimeError(f"Gemini API Error ({e.code}): {error_body}")
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise
