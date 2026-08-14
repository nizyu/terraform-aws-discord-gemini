#!/usr/bin/env python3
"""Discord Application Command Registration Script

Registers or updates the `/ask` slash command with the Discord API.
Supports both Global (all servers) and Guild (instant test on a specific server) registrations.

Usage:
  python scripts/register_commands.py --application-id <APP_ID> --bot-token <BOT_TOKEN> [--guild-id <GUILD_ID>]
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DISCORD_API_BASE = "https://discord.com/api/v10"

COMMAND_PAYLOAD = {
    "name": "ask",
    "description": "Gemini AIに質問や相談をします（スレッドで回答）",
    "options": [
        {
            "name": "prompt",
            "description": "質問・プロンプトの内容",
            "type": 3,  # STRING
            "required": True,
        }
    ],
}


def register_command(application_id: str, bot_token: str, guild_id: str = None) -> None:
    if guild_id:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/guilds/{guild_id}/commands"
        scope_name = f"Guild ({guild_id})"
    else:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/commands"
        scope_name = "Global (All Guilds)"

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }

    data = json.dumps(COMMAND_PAYLOAD).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    print(f"[*] Registering '/ask' command to Discord {scope_name}...")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            res_json = json.loads(res_body)
            print(f"[+] Successfully registered command: {res_json.get('name')} (ID: {res_json.get('id')})")
            if not guild_id:
                print("[i] Note: Global commands may take a few minutes to an hour to propagate.")
            else:
                print("[i] Guild commands update immediately.")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[!] HTTP Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Failed to register command: {e}", file=sys.stderr)
        sys.exit(1)


def list_commands(application_id: str, bot_token: str, guild_id: str = None) -> None:
    if guild_id:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/guilds/{guild_id}/commands"
    else:
        url = f"{DISCORD_API_BASE}/applications/{application_id}/commands"

    headers = {"Authorization": f"Bot {bot_token}"}
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            commands = json.loads(res.read().decode("utf-8"))
            print(f"[+] Found {len(commands)} command(s):")
            for cmd in commands:
                print(f"  - /{cmd.get('name')}: {cmd.get('description')} (ID: {cmd.get('id')})")
    except Exception as e:
        print(f"[!] Failed to list commands: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Register Discord Slash Commands")
    parser.add_argument("--application-id", required=True, help="Discord Application ID")
    parser.add_argument("--bot-token", required=True, help="Discord Bot Token")
    parser.add_argument("--guild-id", default=None, help="Optional Guild (Server) ID for instant testing")
    parser.add_argument("--list", action="store_true", help="List existing commands instead of registering")

    args = parser.parse_args()

    if args.list:
        list_commands(args.application_id, args.bot_token, args.guild_id)
    else:
        register_command(args.application_id, args.bot_token, args.guild_id)


if __name__ == "__main__":
    main()
