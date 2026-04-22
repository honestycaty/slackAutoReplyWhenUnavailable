#!/usr/bin/env python3
"""
Slack Auto-Reply Bot
Automatically replies to DMs when your status indicates you're on leave.
"""

import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

TOKEN = os.getenv("SLACK_USER_TOKEN")
AUTO_REPLY_MESSAGE = os.getenv("AUTO_REPLY_MESSAGE", 
    "Hi! I'm currently on leave. I'll get back to you when I return. Thanks!")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))

if not TOKEN:
    raise SystemExit("❌ SLACK_USER_TOKEN not set. Check your .env file.")

client = WebClient(token=TOKEN)

# Track who we've already replied to (persists across restarts)
REPLIED_FILE = "replied_users.json"

# Keywords that indicate you're on leave
LEAVE_KEYWORDS = [
    "leave", "off", "holiday", "vacation", "away", 
    "out of office", "ooo", "unavailable", "break"
]


def load_replied_users():
    """Load the list of users we've already replied to."""
    if os.path.exists(REPLIED_FILE):
        with open(REPLIED_FILE, "r") as f:
            data = json.load(f)
            return data.get("users", {}), data.get("status_text", "")
    return {}, ""


def save_replied_users(users, status_text):
    """Save the list of users we've replied to."""
    with open(REPLIED_FILE, "w") as f:
        json.dump({"users": users, "status_text": status_text}, f)


def get_my_status():
    """Get your current Slack status."""
    try:
        response = client.users_profile_get()
        profile = response["profile"]
        status_text = profile.get("status_text", "")
        status_emoji = profile.get("status_emoji", "")
        return status_text, status_emoji
    except SlackApiError as e:
        print(f"⚠️  Could not fetch status: {e.response['error']}")
        return "", ""


def is_on_leave(status_text):
    """Check if status indicates you're on leave."""
    if not status_text:
        return False
    status_lower = status_text.lower()
    return any(keyword in status_lower for keyword in LEAVE_KEYWORDS)


def get_my_user_id():
    """Get your own user ID."""
    response = client.auth_test()
    return response["user_id"]


def get_dm_channels():
    """Get all DM channels."""
    channels = []
    cursor = None
    
    while True:
        kwargs = {"types": "im", "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        
        try:
            response = client.conversations_list(**kwargs)
        except SlackApiError as e:
            print(f"⚠️  Could not list DMs: {e.response['error']}")
            break
        
        channels.extend(response["channels"])
        
        if not response.get("has_more"):
            break
        cursor = response["response_metadata"]["next_cursor"]
    
    return channels


def get_recent_messages(channel_id, since_ts):
    """Get messages from a DM since a specific timestamp."""
    try:
        response = client.conversations_history(
            channel=channel_id,
            oldest=since_ts,
            limit=10
        )
        return response["messages"]
    except SlackApiError as e:
        print(f"⚠️  Could not fetch messages: {e.response['error']}")
        return []


def send_auto_reply(channel_id, user_name):
    """Send the auto-reply message."""
    try:
        client.chat_postMessage(
            channel=channel_id,
            text=AUTO_REPLY_MESSAGE
        )
        print(f"  ✅ Sent auto-reply to {user_name}")
        return True
    except SlackApiError as e:
        print(f"  ⚠️  Failed to send reply: {e.response['error']}")
        return False


def get_user_name(user_id):
    """Get a user's display name."""
    try:
        response = client.users_info(user=user_id)
        profile = response["user"]["profile"]
        return profile.get("display_name") or profile.get("real_name") or user_id
    except SlackApiError:
        return user_id


def main():
    print("🤖 Slack Auto-Reply Bot Starting...")
    print(f"   Checking every {CHECK_INTERVAL} seconds")
    print("   Press Ctrl+C to stop\n")
    
    my_user_id = get_my_user_id()
    replied_users, last_status = load_replied_users()
    last_check = time.time()
    
    try:
        while True:
            status_text, status_emoji = get_my_status()
            on_leave = is_on_leave(status_text)
            
            # If status changed, reset replied users
            if status_text != last_status:
                if on_leave:
                    print(f"🏖  Leave mode activated: \"{status_text}\" {status_emoji}")
                    replied_users = {}
                else:
                    print(f"💼 Back to work: \"{status_text}\" {status_emoji}")
                    replied_users = {}
                last_status = status_text
                save_replied_users(replied_users, last_status)
            
            if on_leave:
                # Check all DMs for new messages
                dm_channels = get_dm_channels()
                
                for dm in dm_channels:
                    channel_id = dm["id"]
                    other_user_id = dm["user"]
                    
                    # Skip if we've already replied to this user
                    if other_user_id in replied_users:
                        continue
                    
                    # Get recent messages
                    messages = get_recent_messages(channel_id, str(last_check))
                    
                    # Check if other user sent a message
                    for msg in messages:
                        if msg.get("user") == other_user_id:
                            user_name = get_user_name(other_user_id)
                            print(f"📨 New message from {user_name}")
                            
                            if send_auto_reply(channel_id, user_name):
                                replied_users[other_user_id] = time.time()
                                save_replied_users(replied_users, last_status)
                            break
            
            last_check = time.time()
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n👋 Auto-reply bot stopped.")


if __name__ == "__main__":
    main()
