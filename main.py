from flask import Flask, request
import requests
import datetime
import json
import os
from zoneinfo import ZoneInfo  

# ================================================================
# 🔧 CONFIGURATION
# ================================================================
TELEGRAM_TOKEN = "8439959826:AAHq9KlLaTTLNDxYS7pBaWZZbcLxreqi_0U"
CHAT_ID = "-1002920854933"  
TOPIC_ID = 221
# ================================================================
# 🚀 FLASK APP
# ================================================================
app = Flask(__name__)

def send_message(text: str):
    """Send message to Telegram group."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "message_thread_id": TOPIC_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        print("✅ Sent Telegram message")
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")


@app.route("/", methods=["GET"])
def home():
    return {"status": "running", "service": "GitHub → Telegram Bot"}


@app.route("/github", methods=["POST"])
def github_webhook():
    """Handle GitHub events."""
    data = request.json
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    print(f"📩 Received event: {event_type}")

    repo = data.get("repository", {}).get("full_name", "Unknown Repo")

    # ✅ Get local time in Cambodia
    kh_time = datetime.datetime.now(ZoneInfo("Asia/Phnom_Penh")).strftime("%Y-%m-%d %H:%M:%S")

    # ==============================
    # PUSH EVENT
    # ==============================
    # if event_type == "push":
    #     pusher = data.get("pusher", {}).get("name", "Someone")
    #     branch = data.get("ref", "refs/heads/main").split("/")[-1]
    #     commits = data.get("commits", [])

    #     message = [
    #         f"🧺 *Repo:* {repo}",
    #         f"🎃 *Pushed by:* {pusher}",
    #         f"🌿 *Branch:* `{branch}`",
    #         f"🧭 {kh_time}",
    #         "",
    #         f"🚀 *{len(commits)} commit(s) pushed:*",
    #     ]

    #     for c in commits:
    #         msg = c.get("message", "")
    #         url = c.get("url", "")
    #         author = c.get("author", {}).get("name", "")
    #         message.append(f"• {msg} — _{author}_\n🔗 [View Commit]({url})")

    #     send_message("\n".join(message))
    #     return {"status": "push received"}

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
            msg_full = c.get("message", "").strip()
            msg_first = msg_full.split("\n")[0]  # take only the first line (avoid duplicate “update” lines)
            url = c.get("url", "")
            author = c.get("author", {}).get("name", "")

            # Add spacing and style for merge commits
            if msg_first.startswith("Merge pull request"):
                message.append(f"\n• {msg_first} — _{author}_\n🔗 [View Commit]({url})")
            else:
                message.append(f"• {msg_first} — _{author}_\n🔗 [View Commit]({url})")

        send_message("\n".join(message))
        return {"status": "push received"}


    # ==============================
    # CREATE EVENT (branch/tag)
    # ==============================
    if event_type == "create":
        ref_type = data.get("ref_type")
        ref = data.get("ref", "")
        sender = data.get("sender", {}).get("login", "")
        message = f"🌱 *New {ref_type} created:* `{ref}`\n👤 By: {sender}\n📦 Repo: {repo}\n🕒 {kh_time}"
        send_message(message)
        return {"status": "create received"}

    # ==============================
    # DELETE EVENT
    # ==============================
    if event_type == "delete":
        ref_type = data.get("ref_type")
        ref = data.get("ref", "")
        sender = data.get("sender", {}).get("login", "")
        message = f"🔥 *{ref_type.capitalize()} deleted:* `{ref}`\n👤 By: {sender}\n📦 Repo: {repo}\n🕒 {kh_time}"
        send_message(message)
        return {"status": "delete received"}

    # ==============================
    # PULL REQUEST EVENT
    # ==============================
    # if event_type == "pull_request":
    #     pr = data.get("pull_request", {})
    #     action = data.get("action", "")
    #     merged = pr.get("merged", False)

    #     if action == "closed" and merged:
    #         sender = data.get("sender", {}).get("login", "")
    #         pr_title = pr.get("title", "")
    #         pr_url = pr.get("html_url", "")
    #         message = (
    #             f"✅ *Pull Request Merged!*\n"
    #             f"📦 Repo: {repo}\n"
    #             f"👤 By: {sender}\n"
    #             f"📝 Title: {pr_title}\n"
    #             f"🔗 [View PR]({pr_url})\n"
    #             f"🕒 {kh_time}"
    #         )
    #         send_message(message)
    #         return {"status": "PR merge received"}

    #     else:
    #         print("⚠️ Pull request not merged or closed without merge")
    #         return {"status": "PR not merged"}

    # DEFAULT UNKNOWN EVENT
    print(f"⚠️ Unhandled event: {event_type} from {repo}")
    return {"status": "unhandled event"}


# ================================================================
# 🧰 RUN SERVER
# ================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Server running on port {port}")
    app.run(host="0.0.0.0", port=port)
