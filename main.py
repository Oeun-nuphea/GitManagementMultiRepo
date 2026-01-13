from flask import Flask, request
import requests
import datetime
import os
from zoneinfo import ZoneInfo

# ================================================================
# 🔧 CONFIGURATION
# ================================================================
TELEGRAM_TOKEN = "8036205736:AAGrzVM2AF3qO8HXVqpl_cP0g_0M6zIhgII"
DEFAULT_CHAT_ID = "-4980462929"

app = Flask(__name__)

def send_telegram(text):
    """Utility to send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": DEFAULT_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Telegram Message Sent")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

@app.route("/", methods=["GET"])
def health_check():
    # This is what cron-job.org hits
    now = datetime.datetime.now(ZoneInfo("Asia/Phnom_Penh")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ Keep-alive ping at {now}")
    return {"status": "online", "time_kh": now}

@app.route("/github", methods=["POST"])
def github_webhook():
    event = request.headers.get("X-GitHub-Event", "unknown")
    data = request.json
    repo_name = data.get("repository", {}).get("full_name", "Unknown Repo")
    now = datetime.datetime.now(ZoneInfo("Asia/Phnom_Penh")).strftime("%Y-%m-%d %H:%M:%S")

    print(f"📩 GitHub Event Received: {event}")

    # 1. HANDLE PING (When you click 'Add Webhook')
    if event == "ping":
        msg = f"🔔 *GitHub Webhook Linked!*\n📦 Repo: {repo_name}\n✅ Status: Active\n🕒 {now}"
        send_telegram(msg)
        return "OK", 200

    # 2. HANDLE PUSH
    if event == "push":
        pusher = data.get("pusher", {}).get("name", "Someone")
        branch = data.get("ref", "").split("/")[-1]
        commits = data.get("commits", [])
        
        msg_lines = [
            f"🚀 *New Push to {repo_name}*",
            f"👤 *By:* {pusher}",
            f"🌿 *Branch:* `{branch}`",
            f"🕒 {now}",
            f"\n📝 *{len(commits)} Commits:*",
        ]
        
        for c in commits[:5]: # Limit to 5 commits to avoid long messages
            msg_lines.append(f"• {c.get('message')} (_by {c.get('author', {}).get('name')}_)")

        send_telegram("\n".join(msg_lines))
        return "OK", 200

    return "Ignored Event", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)