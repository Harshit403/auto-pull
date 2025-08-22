import os
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from git import Repo, InvalidGitRepositoryError
import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_PATH = os.getenv('GIT_REPO_PATH')
BRANCH = os.getenv('GIT_BRANCH', 'master')
PORT = int(os.getenv('PORT', 8000))
GIT_USERNAME = os.getenv('GIT_USERNAME')
GIT_REPO_SLUG = os.getenv('GIT_REPO_SLUG')
GIT_PAT = os.getenv('GIT_PAT')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_ID', '').split(',')

app = FastAPI()

def send_telegram_message(message: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        if chat_id.strip():
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                data = {'chat_id': chat_id.strip(), 'text': message, 'parse_mode': 'Markdown'}
                requests.post(url, data=data, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {chat_id}: {str(e)}")

def update_repository():
    try:
        logger.info(f"Attempting to update repository at {REPO_PATH}")
        logger.info(f"Repository slug: {GIT_REPO_SLUG}")
        logger.info(f"Branch: {BRANCH}")
        logger.info(f"Username: {GIT_USERNAME}")
        
        repo = Repo(REPO_PATH)
        
        # Create remote URL with credentials
        remote_url = f"https://{GIT_USERNAME}:{GIT_PAT}@github.com/{GIT_REPO_SLUG}.git"
        logger.info(f"Remote URL: {remote_url.replace(GIT_PAT, '***')}")
        
        origin = repo.remotes.origin
        origin.set_url(remote_url)
        
        logger.info("Fetching changes...")
        origin.fetch()
        
        current_commit = repo.head.commit
        target_commit = origin.refs[BRANCH].commit
        
        if current_commit != target_commit:
            logger.info("Pulling changes...")
            origin.pull()
            logger.info(f"Repository updated to {target_commit.hexsha[:8]}")
            return True, f"Updated to {target_commit.hexsha[:8]}", target_commit.hexsha[:8]
        else:
            logger.info("Repository is already up-to-date")
            return False, "Already up-to-date", None
            
    except InvalidGitRepositoryError:
        error_msg = f"Invalid git repository at {REPO_PATH}"
        logger.error(error_msg)
        return False, error_msg, None
    except Exception as e:
        error_msg = f"Error updating repository: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None

@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        event_type = request.headers.get('X-GitHub-Event')
        logger.info(f"Received event type: {event_type}")
        
        if event_type != 'push':
            return JSONResponse(content={'message': 'Only push events are processed'}, status_code=200)
        
        payload = await request.json()
        ref = payload.get('ref', '')
        logger.info(f"Received push to ref: {ref}")
        
        # Check if this is the correct branch
        if ref != f'refs/heads/{BRANCH}':
            message = f'Push to {ref} ignored, only {BRANCH} is processed'
            logger.info(message)
            return JSONResponse(content={'message': message}, status_code=200)
        
        logger.info("Starting repository update...")
        success, message, commit_hash = update_repository()
        
        if success:
            commits = payload.get('commits', [{}])
            if commits:
                commit_data = commits[0]
                commit_message = commit_data.get('message', 'No message')
                commit_author = commit_data.get('author', {}).get('name', 'Unknown')
                telegram_msg = f"✅ *Repository Updated*\n\n📁 Repository: `{GIT_REPO_SLUG}`\n🌿 Branch: `{BRANCH}`\n📝 Commit: `{commit_hash}`\n👤 Author: `{commit_author}`\n💬 Message: `{commit_message}`"
                send_telegram_message(telegram_msg)
        
        status_code = 200 if success else 500
        logger.info(f"Webhook processing result: {message}")
        return JSONResponse(content={'message': message}, status_code=status_code)
        
    except Exception as e:
        error_msg = f"Webhook processing error: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(content={'message': error_msg}, status_code=500)

@app.get("/")
async def root():
    return {"message": "GitHub Webhook Receiver is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
