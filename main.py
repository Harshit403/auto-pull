import os
import hmac
import hashlib
import logging
import requests
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from git import Repo, InvalidGitRepositoryError
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GITHUB_SECRET = os.getenv('GIT_PAT')
REPO_PATH = os.getenv('GIT_REPO_PATH')
BRANCH = os.getenv('GIT_BRANCH', 'master')
PORT = int(os.getenv('PORT', 8000))
GIT_USERNAME = os.getenv('GIT_USERNAME')
GIT_REPO_SLUG = os.getenv('GIT_REPO_SLUG')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_ID', '').split(',')

app = FastAPI()

def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    hash_object = hmac.new(GITHUB_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

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
        repo = Repo(REPO_PATH)
        remote_url = f"https://{GIT_USERNAME}:{GITHUB_SECRET}@github.com/{GIT_REPO_SLUG}.git"
        origin = repo.remotes.origin
        origin.set_url(remote_url)
        origin.fetch()
        current_commit = repo.head.commit
        target_commit = origin.refs[BRANCH].commit
        if current_commit != target_commit:
            origin.pull()
            logger.info(f"Repository updated to {target_commit.hexsha[:8]}")
            return True, f"Updated to {target_commit.hexsha[:8]}", target_commit.hexsha[:8]
        else:
            logger.info("Repository is already up-to-date")
            return False, "Already up-to-date", None
    except InvalidGitRepositoryError:
        logger.error(f"Invalid git repository at {REPO_PATH}")
        return False, "Invalid repository path", None
    except Exception as e:
        logger.error(f"Error updating repository: {str(e)}")
        return False, str(e), None

@app.post("/webhook")
async def github_webhook(request: Request):
    signature = request.headers.get('X-Hub-Signature-256')
    payload_body = await request.body()
    
    if not verify_signature(payload_body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    
    event_type = request.headers.get('X-GitHub-Event')
    if event_type != 'push':
        return JSONResponse(content={'message': 'Only push events are processed'}, status_code=200)
    
    payload = await request.json()
    ref = payload.get('ref', '')
    if ref != f'refs/heads/{BRANCH}':
        return JSONResponse(content={'message': f'Push to {ref} ignored, only {BRANCH} is processed'}, status_code=200)
    
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
    return JSONResponse(content={'message': message}, status_code=status_code)

@app.get("/")
async def root():
    return {"message": "GitHub Webhook Receiver is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
