<p align="center">
  <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/brands/github.svg" width="60" />
  <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svbrands/telegram.svg" width="60" />
</p>

<h1 align="center">
  GitHub ➜ Telegram Auto-Deploy Webhook
</h1>

<p align="center">
  <strong>Zero-config FastAPI server that pulls your repository on every GitHub push event and pings you on Telegram.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.8+-blue.svg"/>
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.100+-009688.svg"/>
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg"/>
</p>

---

## 🚀 Features
- **Instant deploys** – pulls the latest code on every push  
- **Real-time notifications** – Telegram messages for success / failure  
- **100 % environment driven** – zero code changes between staging & prod  
- **Single-file** – drop into any repo and go  

---

## 📦 Installation

```bash
# 1. Clone or copy this file into your server
git clone https://github.com/your-org/auto-pull-webhook.git
cd auto-pull-webhook

# 2. Create & activate virtual env
python3 -m venv .venv
source .venv/bin/activate

# 3. Install deps
pip install -r requirements.txt   # or: pip install fastapi uvicorn python-dotenv requests
```

---

⚙️ Environment Variables

Create a file named `.env` in the same directory as `main.py`:

```bash
# ============================================
#  REQUIRED – GitHub access
# ============================================
GIT_REPO_PATH=/absolute/path/to/your/project
GIT_REPO_SLUG=your-username/your-repo        # e.g. octocat/Hello-World
GIT_BRANCH=main                              # branch to pull
GIT_USERNAME=your-username
GIT_PAT=ghp_XXXXXXXXXXXXXXXXXXXX             # classic or fine-grained token

# ============================================
#  REQUIRED – Telegram notifications
# ============================================
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOp
TELEGRAM_CHAT_ID=@yourChannelOrUserID        # numeric id or @publicChannel

# ============================================
#  OPTIONAL – Server settings
# ============================================
PORT=8000                                    # defaults to 8000
```

> 🔐 Security tip:

Restrict the PAT to only the repository that needs auto-pull and give it Contents: read & write scope.

---

🏃‍♂️ Running the Server

```bash
# Development
python3 main.py

# Production (systemd, Docker, etc.)
PORT=8080 python3 main.py
```

Server will listen on `0.0.0.0:<PORT>` and print:

```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8080
```

---

🔗 GitHub Webhook Setup

1. Go to your repo ➜ Settings ➜ Webhooks ➜ Add webhook  
2. Payload URL: `http://<your-server-ip>:<PORT>/webhook`  
3. Content type: `application/json`  
4. Events: choose Just the push event  
5. ✅ Active ➜ Add webhook

---

📱 Telegram Messages

Event	Message	
✅ Success	`GitHub repo updated: your-username/your-repo`	
❌ Git error	`Git pull failed:\nfatal: ...`	
❌ Unknown error	`Unexpected error:\n...`	

---

🐳 Docker (one-liner)

```bash
docker run -d \
  --name auto-pull \
  --restart always \
  -e GIT_REPO_PATH=/repo \
  -e GIT_REPO_SLUG=your-username/your-repo \
  -e GIT_BRANCH=main \
  -e GIT_USERNAME=your-username \
  -e GIT_PAT=ghp_XXX \
  -e TELEGRAM_TOKEN=123:ABC \
  -e TELEGRAM_CHAT_ID=@yourChannel \
  -e PORT=8000 \
  -p 8000:8000 \
  -v /host/path/to/repo:/repo \
  python:3.11-slim \
  bash -c "pip install fastapi uvicorn python-dotenv requests && python3 -u /repo/main.py"
```

---

🧪 Testing Manually

```bash
curl -X POST http://localhost:8000/webhook \
     -H "Content-Type: application/json" \
     -d '{"ref":"refs/heads/main"}'
```

---

📄 License

MIT © Harshit Shrivastav
