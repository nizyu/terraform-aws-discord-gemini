"""Discord API Client

Handles Discord REST API v10 operations:
- Editing deferred interaction responses
- Creating threads
- Sending messages to channels/threads
- Message chunking for Discord's 2,000 character limit
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://github.com/nizyu/terraform-aws-discord-gemini, 1.0.0)"
MAX_DISCORD_MESSAGE_LENGTH = 2000


def split_message(text: str, max_length: int = 1900) -> List[str]:
    """Split a long text into chunks that fit within Discord message limits.
    Preserves line breaks and code blocks where possible.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = []
    current_length = 0

    lines = text.split("\n")
    for line in lines:
        line_len = len(line) + 1  # include newline
        if current_length + line_len > max_length:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # If a single line is longer than max_length, force-split it
            while len(line) > max_length:
                chunks.append(line[:max_length])
                line = line[max_length:]

            if line:
                current_chunk.append(line)
                current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


class DiscordClient:
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        use_bot_auth: bool = False,
    ) -> Dict[str, Any]:
        url = f"{DISCORD_API_BASE_URL}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

        if use_bot_auth and self.bot_token:
            headers["Authorization"] = f"Bot {self.bot_token}"

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                body = res.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"Discord API HTTPError {e.code} on {method} {endpoint}: {error_body}")
            raise RuntimeError(f"Discord API Error ({e.code}): {error_body}")
        except Exception as e:
            logger.error(f"Discord API request failed: {e}", exc_info=True)
            raise

    def edit_original_interaction_response(
        self,
        application_id: str,
        interaction_token: str,
        content: str,
    ) -> Dict[str, Any]:
        """Edit the initial deferred interaction response (@original)."""
        endpoint = f"/webhooks/{application_id}/{interaction_token}/messages/@original"
        payload = {"content": content}
        return self._request(endpoint, method="PATCH", payload=payload, use_bot_auth=False)

    def create_followup_message(
        self,
        application_id: str,
        interaction_token: str,
        content: str,
    ) -> Dict[str, Any]:
        """Send a followup message to an interaction."""
        endpoint = f"/webhooks/{application_id}/{interaction_token}"
        payload = {"content": content}
        return self._request(endpoint, method="POST", payload=payload, use_bot_auth=False)

    def create_thread_from_message(
        self,
        channel_id: str,
        message_id: str,
        name: str,
        auto_archive_duration: int = 10080,  # 7 days in minutes
    ) -> Dict[str, Any]:
        """Create a public thread from an existing message."""
        endpoint = f"/channels/{channel_id}/messages/{message_id}/threads"
        payload = {
            "name": name[:100],  # Discord limit: 100 chars
            "auto_archive_duration": auto_archive_duration,
        }
        return self._request(endpoint, method="POST", payload=payload, use_bot_auth=True)

    def create_thread_without_message(
        self,
        channel_id: str,
        name: str,
        auto_archive_duration: int = 10080,
    ) -> Dict[str, Any]:
        """Create a thread directly in a guild channel (type 11: GUILD_PUBLIC_THREAD)."""
        endpoint = f"/channels/{channel_id}/threads"
        payload = {
            "name": name[:100],
            "auto_archive_duration": auto_archive_duration,
            "type": 11,
        }
        return self._request(endpoint, method="POST", payload=payload, use_bot_auth=True)

    def send_channel_message(
        self,
        channel_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """Send a message to a channel or thread."""
        endpoint = f"/channels/{channel_id}/messages"
        payload = {"content": content}
        return self._request(endpoint, method="POST", payload=payload, use_bot_auth=True)
