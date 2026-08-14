"""Discord Ingress Lambda Handler

Handles Discord Interactions HTTP Webhooks:
- Verifies Ed25519 signatures
- Responds to PING (type: 1)
- Receives APPLICATION_COMMAND (type: 2, e.g., /ask)
- Writes initial request to DynamoDB with status 'PENDING'
- Returns DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE (type: 5) within 3 seconds
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
import boto3
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "")
TTL_DAYS = int(os.environ.get("TTL_DAYS", "7"))

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME) if DYNAMODB_TABLE_NAME else None

# Discord Interaction Types
INTERACTION_TYPE_PING = 1
INTERACTION_TYPE_APPLICATION_COMMAND = 2

# Discord Response Types
RESPONSE_TYPE_PONG = 1
RESPONSE_TYPE_DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5

# Discord Thread Channel Types: 10 = News Thread, 11 = Public Thread, 12 = Private Thread
THREAD_CHANNEL_TYPES = {10, 11, 12}


def verify_discord_signature(signature: str, timestamp: str, body: str, public_key: str) -> bool:
    """Verify Discord Ed25519 signature."""
    if not signature or not timestamp or not public_key:
        return False
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError) as err:
        logger.warning(f"Signature verification failed: {err}")
        return False


def get_header(headers: dict, key: str) -> str:
    """Case-insensitive header getter."""
    if not headers:
        return ""
    key_lower = key.lower()
    for k, v in headers.items():
        if k.lower() == key_lower:
            return v
    return ""


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    headers = event.get("headers", {})
    body = event.get("body", "")

    # Handle base64 encoded body if needed
    if event.get("isBase64Encoded", False):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    # 1. Signature Verification
    signature = get_header(headers, "x-signature-ed25519")
    timestamp = get_header(headers, "x-signature-timestamp")

    if not verify_discord_signature(signature, timestamp, body, DISCORD_PUBLIC_KEY):
        logger.error("Invalid request signature")
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "invalid request signature"}),
        }

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "invalid JSON body"}),
        }

    interaction_type = data.get("type")

    # 2. Handle PING
    if interaction_type == INTERACTION_TYPE_PING:
        logger.info("Responding to PING")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"type": RESPONSE_TYPE_PONG}),
        }

    # 3. Handle APPLICATION_COMMAND (/ask)
    if interaction_type == INTERACTION_TYPE_APPLICATION_COMMAND:
        command_data = data.get("data", {})
        command_name = command_data.get("name")
        interaction_id = data.get("id")
        interaction_token = data.get("token")
        application_id = data.get("application_id")
        channel_id = data.get("channel_id")
        guild_id = data.get("guild_id")

        # Get channel details
        channel = data.get("channel", {})
        channel_type = channel.get("type")
        is_thread = channel_type in THREAD_CHANNEL_TYPES

        # User details
        member = data.get("member", {})
        user = member.get("user") or data.get("user", {})
        user_id = user.get("id", "")
        user_name = user.get("global_name") or user.get("username", "Unknown")

        # Parse command options (prompt)
        prompt = ""
        for opt in command_data.get("options", []):
            if opt.get("name") == "prompt":
                prompt = opt.get("value", "")
                break

        logger.info(
            f"Command received: name={command_name}, channel_id={channel_id}, "
            f"is_thread={is_thread}, user={user_name}, prompt_length={len(prompt)}"
        )

        now_ts = int(time.time())
        now_iso = datetime.now(timezone.utc).isoformat()
        ttl = now_ts + (TTL_DAYS * 86400)

        # If inside a thread, session_id is thread_id. If in main channel, temporary session_id is req_<id>
        if is_thread:
            session_id = channel_id
            is_new_thread = False
        else:
            session_id = f"req_{interaction_id}"
            is_new_thread = True

        # Save to DynamoDB
        if table:
            item = {
                "session_id": session_id,
                "status": "PENDING",
                "is_new_thread": is_new_thread,
                "channel_id": channel_id,
                "channel_type": channel_type or 0,
                "guild_id": guild_id or "",
                "interaction_id": interaction_id,
                "interaction_token": interaction_token,
                "application_id": application_id,
                "user_id": user_id,
                "user_name": user_name,
                "prompt": prompt,
                "created_at": now_iso,
                "updated_at": now_iso,
                "ttl": ttl,
            }
            try:
                table.put_item(Item=item)
                logger.info(f"Saved pending interaction to DynamoDB: session_id={session_id}")
            except Exception as e:
                logger.error(f"Failed to put item to DynamoDB: {e}", exc_info=True)
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Database error"}),
                }

        # 4. Immediate Deferred Response (Thinking...)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"type": RESPONSE_TYPE_DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE}),
        }

    return {
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Unsupported interaction type"}),
    }
