# Slack Auto-Reply (Leave Mode)

Automatically replies to Slack DMs when your status indicates you're on leave.

## How it works

1. Runs in the background, checking for new DMs every 60 seconds
2. Reads your current Slack status
3. If your status contains leave keywords (e.g. "leave", "off", "holiday"), it auto-replies
4. Won't spam — only replies once per person per leave period
5. Stops auto-replying when your status is back to normal

## Setup

### 1. Slack App & Token

You need a **User Token** (`xoxp-`) with these scopes in **OAuth & Permissions**:

- `users.profile:read` — to read your status
- `im:history` — to read DMs
- `im:write` — to send replies
- `chat:write` — to send messages

Go to https://api.slack.com/apps → your app → OAuth & Permissions → add scopes → reinstall app.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` with your token and custom message.

### 4. Run

```bash
python auto_reply.py
```

Keep it running in the background. Stop it with `Ctrl+C`.

## Setting your Slack status

Just set your Slack status to anything containing leave keywords:
- "On Leave"
- "Annual Leave"
- "Public Holiday"
- "Out of Office"
- "On Vacation"

The bot will detect it automatically!
