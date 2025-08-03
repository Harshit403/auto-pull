import os
import subprocess
import requests
import uvicorn
from fastapi import FastAPI, Request, status
from dotenv import load_dotenv
from fastapi.responses import PlainTextResponse
from datetime import datetime

load_dotenv()

# Settings
GIT_REPO_PATH = os.getenv("GIT_REPO_PATH")
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_PAT = os.getenv("GIT_PAT")
GIT_REPO_SLUG = os.getenv("GIT_REPO_SLUG")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOG_FILE_PATH = os.path.join(os.getcwd(), "git_logs.txt")

app = FastAPI()

def notify_telegram(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        os.chdir(GIT_REPO_PATH)

        # Log start
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"\n\n---- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ----\n")
            log_file.write("Starting git pull...\n")

            # Optionally set origin URL if credentials provided
            if GIT_USERNAME and GIT_PAT and GIT_REPO_SLUG:
                remote_url = f"https://{GIT_USERNAME}:{GIT_PAT}@github.com/{GIT_REPO_SLUG}.git"
                subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)

            # Start pull process
            process = subprocess.Popen(
                ["git", "pull", "origin", GIT_BRANCH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            while True:
                output = process.stdout.readline().decode("utf-8")
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log_file.write(output.strip() + "\n")

            err_output = process.stderr.read().decode("utf-8")
            if err_output:
                log_file.write(f"Error: {err_output}\n")

            log_file.write("Git pull completed.\n")

        notify_telegram(f"✅ Git pull successful: `{GIT_REPO_SLUG or 'Local repo'}`")
        return PlainTextResponse("Git pull completed", status_code=200)

    except Exception as e:
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(f"Error: {str(e)}\n")
        notify_telegram(f"❌ Git pull failed:\n{str(e)}")
        return PlainTextResponse("Error occurred", status_code=500)

@app.get("/")
async def root():
    return {"message": "Webhook is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
