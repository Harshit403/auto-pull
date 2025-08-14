import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from fastapi.responses import PlainTextResponse
from datetime import datetime

load_dotenv()

GIT_REPO_PATH = os.getenv("GIT_REPO_PATH")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_PAT = os.getenv("GITHUB_PAT")
GITHUB_REPO_SLUG = os.getenv("GITHUB_REPO_SLUG")
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOG_FILE_PATH = os.path.join(os.getcwd(), "git_logs.txt")

app = FastAPI()

def notify_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception:
        pass

@app.post("/webhook")
async def github_webhook(request: Request):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        os.chdir(GIT_REPO_PATH)

        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"\n\n---- {timestamp} ----\n")
            log_file.write("Starting git pull...\n")

        if GITHUB_USERNAME and GITHUB_PAT and GITHUB_REPO_SLUG:
            remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_PAT}@github.com/{GITHUB_REPO_SLUG}.git"
            os.system(f'git remote set-url origin {remote_url}')

        pull_output = os.popen(f'git pull origin {GIT_BRANCH}').read()

        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"Pull Output:\n{pull_output}\n")
            log_file.write("Git pull completed.\n")

        notify_telegram(f"✅ Git pull successful on `{GIT_BRANCH}` for `{GITHUB_REPO_SLUG or 'repo'}`")
        return PlainTextResponse("Git pull completed", status_code=200)

    except Exception as e:
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"[{timestamp}] Error: {str(e)}\n")
        notify_telegram(f"❌ Git pull failed on `{GIT_BRANCH}`:\n{str(e)}")
        return PlainTextResponse("Error occurred", status_code=500)

@app.get("/")
async def root():
    return {"message": "Webhook is running"}
