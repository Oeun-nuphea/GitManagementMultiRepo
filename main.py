from flask import Flask, request, jsonify
import requests
import datetime
import os
from zoneinfo import ZoneInfo  # Python 3.9+

# ================================================================
# 🔧 CONFIGURATION
# ================================================================
# TELEGRAM_TOKEN = "8098069455:AAFXMerG7ofl9Rzwfp5dOBUZGoXuTaA8znI"
TELEGRAM_TOKEN = "8036205736:AAGrzVM2AF3qO8HXVqpl_cP0g_0M6zIhgII" 
DEFAULT_CHAT_ID = "-4980462929"

# Optional: map specific repos to specific Telegram chats
REPO_CHATS = {
    # "username/repo_name": "chat_id",
    # Example:
    # "user/repo1": "-1111111111",
    # "user/repo2": "-2222222222",
}

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# ================================================================
# 🚀 FLASK APP
# ================================================================
app = Flask(__name__)

def send_message(repo: str, text: str):
    """Send message to Telegram group."""
    chat_id = REPO_CHATS.get(repo, DEFAULT_CHAT_ID)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(TELEGRAM_API, json=payload, timeout=10)
        res.raise_for_status()
        print(f"✅ Sent Telegram message for {repo}")
    except Exception as e:
        print(f"❌ Telegram send failed for {repo}: {e}")


@app.route("/", methods=["GET"])
def home():
    return {"status": "running", "service": "GitHub → Telegram Bot (Multi-Repo)"}


@app.route("/github", methods=["POST"])
def github_webhook():
    """Handle GitHub events from any repo."""
    data = request.json
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    repo = data.get("repository", {}).get("full_name", "Unknown Repo")
    print(f"📩 Received event: {event_type} from {repo}")

    # Get local time in Cambodia
    kh_time = datetime.datetime.now(ZoneInfo("Asia/Phnom_Penh")).strftime("%Y-%m-%d %H:%M:%S")

    # ==============================
    # PUSH EVENT
    # ==============================
    if event_type == "push":
        pusher = data.get("pusher", {}).get("name", "Someone")
        branch = data.get("ref", "refs/heads/main").split("/")[-1]
        commits = data.get("commits", [])

        message = [
            f"🧺 *Repo:* {repo}",
            f"🎃 *Pushed by:* {pusher}",
            f"🌿 *Branch:* `{branch}`",
            f"🧭 {kh_time}",
            "",
            f"🚀 *{len(commits)} commit(s) pushed:*",
        ]

        for c in commits:
            msg = c.get("message", "")
            url = c.get("url", "")
            author = c.get("author", {}).get("name", "")
            message.append(f"• {msg} — _{author}_\n🔗 [View Commit]({url})")

        send_message(repo, "\n".join(message))
        return {"status": "push received"}

    # ==============================
    # CREATE EVENT
    # ==============================
    if event_type == "create":
        ref_type = data.get("ref_type", "")
        ref = data.get("ref", "")
        sender = data.get("sender", {}).get("login", "")
        message = f"🌱 *New {ref_type} created:* `{ref}`\n👤 By: {sender}\n📦 Repo: {repo}\n🕒 {kh_time}"
        send_message(repo, message)
        return {"status": "create received"}

    # ==============================
    # DELETE EVENT
    # ==============================
    if event_type == "delete":
        ref_type = data.get("ref_type", "")
        ref = data.get("ref", "")
        sender = data.get("sender", {}).get("login", "")
        message = f"🔥 *{ref_type.capitalize()} deleted:* `{ref}`\n👤 By: {sender}\n📦 Repo: {repo}\n🕒 {kh_time}"
        send_message(repo, message)
        return {"status": "delete received"}

    # ==============================
    # UNKNOWN EVENT
    # ==============================
    send_message(repo, f"ℹ️ *Unhandled event:* `{event_type}` from *{repo}*\n🕒 {kh_time}")
    return {"status": "unhandled event"}

# ================================================================
# 🧰 RUN SERVER
# ================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Server running on port {port}")
    app.run(host="0.0.0.0", port=port)
