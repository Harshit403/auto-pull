import os
import subprocess
import requests
from fastapi import FastAPI, Request, status
from dotenv import load_dotenv
from fastapi.responses import PlainTextResponse

load_dotenv()

# GitHub settings
GIT_REPO_PATH = os.getenv("GIT_REPO_PATH")
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_PAT = os.getenv("GIT_PAT")
GIT_REPO_SLUG = os.getenv("GIT_REPO_SLUG")

# Telegram settings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI()

def notify_telegram(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

@app.post("/webhook")
async def github_webhook(req: Request):
    try:
        # Setup remote with token
        remote_url = f"https://{GIT_USERNAME}:{GIT_PAT}@github.com/{GIT_REPO_SLUG}.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=GIT_REPO_PATH, check=True)

        # Pull latest changes
        subprocess.run(["git", "fetch", "origin"], cwd=GIT_REPO_PATH, check=True)
        subprocess.run(["git", "reset", "--hard", f"origin/{GIT_BRANCH}"], cwd=GIT_REPO_PATH, check=True)

        notify_telegram(f"✅ GitHub repo updated: `{GIT_REPO_SLUG}`")
        return PlainTextResponse("Update successful", status_code=status.HTTP_200_OK)

    except subprocess.CalledProcessError as e:
        error = e.stderr.decode() if e.stderr else str(e)
        notify_telegram(f"❌ Git pull failed:\n{error}")
        return PlainTextResponse("Git error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        notify_telegram(f"❌ Unexpected error:\n{str(e)}")
        return PlainTextResponse("Server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
