"""Discord Gemini Worker Lambda Handler

Processes DynamoDB Stream events:
- Triggers only when status is 'PENDING' (prevents infinite loops)
- Retrieves multi-turn conversation context from DynamoDB
- Calls Google Gemini API
- Creates Discord thread on new prompt or replies in existing thread
- Updates DynamoDB context, status to 'COMPLETED', and resets TTL
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
import boto3
from boto3.dynamodb.types import TypeDeserializer

from discord_client import DiscordClient, split_message
from gemini_client import GeminiClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "")
TTL_DAYS = int(os.environ.get("TTL_DAYS", "7"))

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME) if DYNAMODB_TABLE_NAME else None
deserializer = TypeDeserializer()

gemini = GeminiClient(api_key=GEMINI_API_KEY, model=GEMINI_MODEL)
discord = DiscordClient(bot_token=DISCORD_BOT_TOKEN)


def deserialize_dynamodb_image(image: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DynamoDB low-level JSON into Python dict."""
    return {k: deserializer.deserialize(v) for k, v in image.items()}


def process_record(record_data: Dict[str, Any]) -> None:
    session_id = record_data.get("session_id", "")
    is_new_thread = record_data.get("is_new_thread", False)
    channel_id = record_data.get("channel_id", "")
    application_id = record_data.get("application_id", "")
    interaction_token = record_data.get("interaction_token", "")
    prompt = record_data.get("prompt", "")
    user_name = record_data.get("user_name", "User")

    logger.info(
        f"Processing session_id={session_id}, is_new_thread={is_new_thread}, "
        f"prompt_length={len(prompt)}"
    )

    # 1. Mark status as PROCESSING to prevent duplicate concurrent runs
    now_iso = datetime.now(timezone.utc).isoformat()
    now_ts = int(time.time())
    ttl = now_ts + (TTL_DAYS * 86400)

    if table:
        try:
            table.update_item(
                Key={"session_id": session_id},
                UpdateExpression="SET #s = :processing, updated_at = :now",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":processing": "PROCESSING", ":now": now_iso},
            )
        except Exception as e:
            logger.warning(f"Failed to update status to PROCESSING: {e}")

    try:
        # 2. Retrieve existing context if continuing in a thread
        context: List[Dict[str, Any]] = []
        if not is_new_thread:
            if table:
                try:
                    res = table.get_item(Key={"session_id": session_id})
                    existing_item = res.get("Item", {})
                    raw_context = existing_item.get("context", [])
                    if isinstance(raw_context, list) and raw_context:
                        context = raw_context
                except Exception as db_err:
                    logger.warning(f"Failed to fetch session from DynamoDB: {db_err}")

            # If no DynamoDB context found (e.g. human-created thread or expired session),
            # dynamically rebuild conversation context from Discord thread messages!
            if not context and channel_id:
                try:
                    raw_messages = discord.get_channel_messages(channel_id=channel_id, limit=15)
                    if raw_messages:
                        # Sort chronologically (oldest to newest)
                        sorted_messages = sorted(raw_messages, key=lambda m: int(m.get("id", "0")))
                        for msg in sorted_messages:
                            msg_content = msg.get("content", "").strip()
                            author_info = msg.get("author", {})
                            author_name = author_info.get("global_name") or author_info.get("username") or "User"
                            is_bot = author_info.get("bot", False)

                            # Skip empty messages or placeholder messages
                            if not msg_content or "考え中" in msg_content:
                                continue

                            role = "model" if is_bot else "user"
                            formatted_text = msg_content if role == "model" else f"{author_name}: {msg_content}"
                            context.append({
                                "role": role,
                                "parts": [{"text": formatted_text}],
                            })
                        logger.info(f"Rebuilt context from {len(context)} Discord thread messages")
                except Exception as thread_err:
                    logger.warning(f"Failed to retrieve thread history from Discord API: {thread_err}")

        # 3. Generate response with Gemini API
        system_instruction = (
            "あなたは家族向けのDiscordサーバーに常駐する親切でフレンドリーなAIアシスタントです。"
            "家族の会話を助け、丁寧かつわかりやすく自然な日本語で回答してください。"
        )
        reply_text, updated_context = gemini.generate_response(
            prompt=prompt,
            context=context,
            system_instruction=system_instruction,
        )

        # Format quoted prompt
        quoted_prompt = "\n".join(f"> {line}" for line in prompt.splitlines())

        # 4. Handle Discord responses
        if is_new_thread:
            # First, update the original interaction message with full quoted prompt
            prompt_preview = (prompt[:35] + "...") if len(prompt) > 35 else prompt
            summary_msg = f"💬 **{user_name} さんの質問:**\n{quoted_prompt}\n\n🧵 *スレッドで回答しています...*"
            orig_msg = discord.edit_original_interaction_response(
                application_id=application_id,
                interaction_token=interaction_token,
                content=summary_msg,
            )

            orig_message_id = orig_msg.get("id")
            thread_name = f"💬 {user_name}: {prompt_preview}"

            thread_obj = None
            if orig_message_id and channel_id:
                try:
                    thread_obj = discord.create_thread_from_message(
                        channel_id=channel_id,
                        message_id=orig_message_id,
                        name=thread_name,
                    )
                except Exception as err:
                    logger.warning(f"Failed to create thread from message, trying direct thread: {err}")

            if not thread_obj and channel_id:
                thread_obj = discord.create_thread_without_message(
                    channel_id=channel_id,
                    name=thread_name,
                )

            thread_id = thread_obj.get("id") if thread_obj else channel_id

            # Post answers in thread
            chunks = split_message(reply_text)
            for chunk in chunks:
                discord.send_channel_message(channel_id=thread_id, content=chunk)

            # Save thread session in DynamoDB
            if table:
                new_session_item = {
                    "session_id": thread_id,
                    "channel_id": thread_id,
                    "parent_channel_id": channel_id,
                    "prompt": prompt,
                    "last_response": reply_text,
                    "context": updated_context,
                    "status": "COMPLETED",
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "ttl": ttl,
                }
                table.put_item(Item=new_session_item)
                logger.info(f"Saved new thread session: thread_id={thread_id}")

                # Mark temporary request as COMPLETED
                table.update_item(
                    Key={"session_id": session_id},
                    UpdateExpression="SET #s = :completed, updated_at = :now",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":completed": "COMPLETED", ":now": now_iso},
                )

        else:
            # In existing thread: include user's prompt so it is preserved in chat history
            full_response = f"💬 **{user_name}:**\n{quoted_prompt}\n\n🤖 **Gemini:**\n{reply_text}"
            chunks = split_message(full_response)
            first_chunk = chunks[0] if chunks else "回答を取得できませんでした。"
            discord.edit_original_interaction_response(
                application_id=application_id,
                interaction_token=interaction_token,
                content=first_chunk,
            )

            # Send remaining chunks as followups if any
            for extra_chunk in chunks[1:]:
                discord.create_followup_message(
                    application_id=application_id,
                    interaction_token=interaction_token,
                    content=extra_chunk,
                )

            # Update context in DynamoDB
            if table:
                table.update_item(
                    Key={"session_id": session_id},
                    UpdateExpression="SET #s = :completed, #ctx = :ctx, last_response = :last_res, updated_at = :now, #t = :ttl",
                    ExpressionAttributeNames={"#s": "status", "#ctx": "context", "#t": "ttl"},
                    ExpressionAttributeValues={
                        ":completed": "COMPLETED",
                        ":ctx": updated_context,
                        ":last_res": reply_text,
                        ":now": now_iso,
                        ":ttl": ttl,
                    },
                )
                logger.info(f"Updated thread session: session_id={session_id}")

    except Exception as e:
        logger.error(f"Error processing session {session_id}: {e}", exc_info=True)
        # Inform Discord user about error
        try:
            discord.edit_original_interaction_response(
                application_id=application_id,
                interaction_token=interaction_token,
                content="⚠️ 応答の生成中にエラーが発生しました。しばらく経ってから再度お試しください。",
            )
        except Exception as notify_err:
            logger.warning(f"Failed to send error message to Discord: {notify_err}")

        if table:
            try:
                table.update_item(
                    Key={"session_id": session_id},
                    UpdateExpression="SET #s = :err, updated_at = :now",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":err": "ERROR", ":now": now_iso},
                )
            except Exception:
                pass


def lambda_handler(event, context):
    logger.info("Received DynamoDB Stream event: %s", json.dumps(event))

    records = event.get("Records", [])
    for record in records:
        event_name = record.get("eventName")
        if event_name not in ("INSERT", "MODIFY"):
            continue

        dynamodb_data = record.get("dynamodb", {})
        new_image_raw = dynamodb_data.get("NewImage")
        if not new_image_raw:
            continue

        # Check status before full deserialization to avoid unnecessary overhead
        status_val = new_image_raw.get("status", {}).get("S")
        if status_val != "PENDING":
            logger.info(f"Skipping record with status={status_val}")
            continue

        record_dict = deserialize_dynamodb_image(new_image_raw)
        process_record(record_dict)

    return {"statusCode": 200, "body": "OK"}
