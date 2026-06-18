# 🤖 GenAI Code Review Copilot

An autonomous, self-learning Code Review Copilot built with FastAPI, LangChain, and Google Gemini. It reviews Pull Requests in real-time, enforces repository-specific house rules using RAG (Retrieval-Augmented Generation), and automatically learns conventions from past merged PRs.

---

## ✨ Features
* **Real-Time PR Review:** Intercepts GitHub Webhooks to analyze code diffs instantly.
* **Inline GitHub Comments:** Posts contextual, severity-tagged suggestions directly to the exact line of code in the PR.
* **Multi-Environment RAG:** Uses local ChromaDB for development and serverless Pinecone for production.
* **Matryoshka Vector Compression:** Utilizes Google's native SDK to compress 3072-dimension embeddings into 1024 dimensions, saving database costs.
* **Background History Ingestion:** Asynchronously scrapes merged PR history to learn implicit team coding conventions without blocking the webhook thread.
* **Multi-Tenant Data Isolation:** Strictly isolates rules based on the `Owner/Repo_Name` namespace.

---

## 🏗️ Architecture Stack
* **Framework:** FastAPI, Python 3.11
* **AI/LLM:** Google Gemini 2.5 Flash, Gemini Embeddings 001
* **Vector DB:** Pinecone (Prod) / ChromaDB (Dev)
* **Orchestration:** LangChain
* **Containerization:** Docker & Docker Compose

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* **Docker and Docker Compose** installed.
* **Google Gemini API Key**: Get a free or paid API key from [Google AI Studio](https://aistudio.google.com/). (Required for embeddings and code review reasoning in both dev/prod).
* **GitHub Personal Access Token (PAT)**:
  * **Fine-Grained Token (Recommended)**:
    * Select your target repositories.
    * Grant **Repository permissions**:
      * **Pull requests**: `Read and Write` (to fetch diffs and post review comments).
      * **Contents**: `Read-only` (to access code files).
      * **Metadata**: `Read-only` (automatically added).
  * **Classic Token**:
    * Check the `repo` scope.
* **ngrok** (Optional): Required for local development to expose the webhook to GitHub. Install via `brew install ngrok/ngrok/ngrok` (macOS) or download from [ngrok.com](https://ngrok.com/).

### 2. Environment Variables (.env Setup)
Duplicate the example environment file:
```bash
cp .env.example .env
```

Open `.env` and configure the following variables:
```env
# GitHub & Gemini Settings
GITHUB_TOKEN=github_pat_xxx
GEMINI_API_KEY=AIzaSyxxx
WEBHOOK_SECRET=your_custom_webhook_secret_string

# Environment Mode
ENVIRONMENT=development # Set to 'production' to route to Pinecone

# Production Settings (Optional)
PINECONE_API_KEY=your_pinecone_key
```

> [!TIP]
> **Generating a secure WEBHOOK_SECRET:**
> You can generate a cryptographically secure 32-byte hexadecimal string using:
> * **macOS/Linux**: `openssl rand -hex 32`
> * **Python**: `python -c "import secrets; print(secrets.token_hex(32))"`

### 3. Local Webhook Tunneling (ngrok)
To test locally, start an HTTP tunnel forwarding to port `8000`:
```bash
ngrok http 8000
```
Copy the secure forwarding URL (e.g. `https://xxxx-xx-xx-xx-xx.ngrok-free.app`). Your webhook URL will be:
`https://xxxx-xx-xx-xx-xx.ngrok-free.app/webhook/github`

### 4. Build and Run
Start the FastAPI server and local ChromaDB containers:
```bash
docker-compose up --build -d
```
* The FastAPI server is available at: http://localhost:8000
* Interactive API documentation (Swagger UI) is available at: http://localhost:8000/docs

---

## 🛠️ Webhook Configuration on GitHub

Configure your GitHub repository to stream Pull Request events to the API:

1. Go to your GitHub Repository -> **Settings** -> **Webhooks** -> **Add webhook**.
2. **Payload URL**: Paste the URL generated in the ngrok step (e.g., `https://xxxx-xx-xx-xx-xx.ngrok-free.app/webhook/github`) or your public domain.
3. **Content type**: Select `application/json` (Do **not** use `application/x-www-form-urlencoded`).
4. **Secret**: Enter the exact `WEBHOOK_SECRET` string from your `.env` file.
5. **Which events would you like to trigger this webhook?**:
   * Select **Let me select individual events**.
   * Check **Pull requests**.
   * Uncheck all other events.
6. Click **Add webhook** to save.

---

## Manual Rule Injection
You can manually teach the AI a new rule using the Swagger UI or via cURL:

```bash
curl -X 'POST' \
  'http://localhost:8000/conventions/learn' \
  -H 'Content-Type: application/json' \
  -d '{
  "rule": "All print statements must be replaced with logging.info()",
  "repo_name": "YourOwner/YourRepo"
}'
```

---

## Automatic History Learning

The moment a new PR is opened or synchronized, the API will immediately trigger a background task to scrape that repository's last 10 merged PRs, extract the underlying house rules using AI, and save them to the database for future reviews.

---

## 🛡️ Security
This application implements HMAC SHA256 signature validation to ensure all incoming webhooks are strictly authenticated by GitHub, preventing unauthorized access or abuse.