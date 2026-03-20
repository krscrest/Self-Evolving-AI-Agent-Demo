# 🔄 Self-Evolving AI Agent Demo

A real-time demonstration of an AI agent that **autonomously improves its own prompts** to extract increasingly accurate information from insurance documents — powered by Azure OpenAI (GPT-4o) and Azure Document Intelligence.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-0078D4?logo=microsoft-azure&logoColor=white)
![Azure AI](https://img.shields.io/badge/Azure_Document_Intelligence-0078D4?logo=microsoft-azure&logoColor=white)

---

## 🎯 What Does This Demo Do?

This application showcases **self-optimizing AI** — an agent that starts with a deliberately weak, generic prompt and iteratively rewrites its own system prompt to dramatically improve output quality.

### The Problem
A generic prompt like *"Summarize this document"* produces shallow, incomplete summaries of complex insurance documents — missing critical details like policy numbers, coverage limits, and endorsements.

### The Solution
Three specialized AI agents work together in a loop:

1. **Analyzer Agent** — Reads an insurance Certificate of Insurance (CoI) using the current system prompt and produces a summary.
2. **Evaluator Agent** — Scores the summary against a detailed 100-point rubric covering 10 categories (named insured, policy numbers, coverage limits, etc.).
3. **Optimizer Agent** — Reads the scores and feedback, then rewrites the system prompt to address weaknesses.

This loop runs **3 cycles**, and you can watch the score climb in real-time as the AI teaches itself to be better.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (UI)                         │
│         Real-time SSE stream  ←──── FastAPI             │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                  Orchestrator                           │
│          (runs the 3-cycle optimization loop)           │
└──┬──────────────────┬──────────────────┬────────────────┘
   │                  │                  │
   ▼                  ▼                  ▼
┌──────────┐   ┌─────────────┐   ┌─────────────┐
│ Analyzer │   │  Evaluator  │   │  Optimizer  │
│  Agent   │   │   Agent     │   │   Agent     │
│          │   │             │   │             │
│ Reads doc│   │ Scores the  │   │ Rewrites    │
│ produces │   │ summary on  │   │ the system  │
│ summary  │   │ 10-category │   │ prompt to   │
│          │   │ rubric      │   │ fix gaps    │
└──────────┘   └─────────────┘   └─────────────┘
      │                                  │
      └──────────── GPT-4o ──────────────┘

┌─────────────────────────────────────────────────────────┐
│           Azure Document Intelligence                   │
│     (PDF parsing with OCR, tables, layout analysis)     │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
├── app/
│   ├── main.py                 # FastAPI app, routes, SSE streaming
│   ├── config.py               # Environment-based configuration with validation
│   ├── auth.py                 # Session-based authentication
│   ├── models.py               # Pydantic data models
│   ├── agents/
│   │   ├── orchestrator.py     # Main optimization loop (3 cycles)
│   │   ├── analyzer.py         # Document analysis agent + initial prompt
│   │   ├── evaluator.py        # Scoring agent with 100-point rubric
│   │   └── optimizer.py        # Prompt rewriting agent
│   └── services/
│       ├── azure_openai.py     # Azure OpenAI client (Entra ID auth)
│       └── document_parser.py  # Azure Document Intelligence PDF parser
├── static/
│   ├── index.html              # Single-page app UI
│   ├── app.js                  # Frontend logic (SSE handling, charts)
│   └── styles.css              # Dark-themed responsive UI
├── .env.example                # Template for required environment variables
├── requirements.txt            # Python dependencies
├── startup.sh                  # Azure App Service startup script
└── planeplus-explorer-internationalgroup-samplecontract.pdf
                                # Sample Certificate of Insurance
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Azure OpenAI** resource with a GPT-4o deployment
- **Azure Document Intelligence** resource
- Azure credentials configured (for Entra ID / `DefaultAzureCredential`)

### 1. Clone the Repository

```bash
git clone https://github.com/krscrest/Self-Evolving-AI-Agent-Demo.git
cd Self-Evolving-AI-Agent-Demo
```

### 2. Set Up Environment

```bash
# Create and activate a virtual environment
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in **all** values:

```env
# Azure Services
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-06-01

AZURE_DOC_INTELLIGENCE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=<your-key>

# App Settings
SECRET_KEY=<generate-a-random-secret>

# Login Credentials
LOGIN_USERNAME=<your-username>
LOGIN_PASSWORD=<your-password>
```

> ⚠️ The app will **fail at startup** with a clear error if any required variable is missing.

### 4. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** in your browser.

### 5. Use the Demo

1. **Log in** with the credentials you set in `.env`
2. Click **"Use Sample Certificate of Insurance"** (or upload your own PDF)
3. Click **"Start Self-Optimization"**
4. Watch the three cycles run in real-time — scores, prompts, and agent activity stream live to the UI

---

## ☁️ Deploy to Azure App Service

The repo includes a `startup.sh` for Azure App Service deployment:

```bash
# The startup script runs:
pip install -r requirements.txt
gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
```

Set all `.env` variables as **Application Settings** in the Azure Portal under your App Service → Configuration.

---

## 📊 Evaluation Rubric (100 Points)

The Evaluator Agent scores every summary against this rubric:

| Category | Max Points | What It Checks |
|----------|-----------|----------------|
| Named Insured | 10 | Full legal name, DBA, complete address |
| Policy Numbers | 10 | All policy numbers captured |
| Insurance Carrier | 10 | Carrier names, NAIC numbers |
| Coverage Types | 10 | GL, Auto, Umbrella, WC, etc. |
| Coverage Limits | 15 | Per-occurrence, aggregate, per-policy limits |
| Effective & Expiration Dates | 10 | Start/end dates for each policy |
| Certificate Holder | 10 | Full name, address, relationship |
| Additional Insured | 10 | Status and applicable policies |
| Subrogation Waiver | 5 | Waiver status and applicable policies |
| Special Conditions | 10 | Endorsements, exclusions, special provisions |

---

## 🔐 Security Notes

- **No secrets in code** — all credentials are loaded from environment variables
- `.env` is excluded via `.gitignore` and never committed
- Authentication uses server-side session tokens (`httponly`, `samesite=strict` cookies)
- Azure OpenAI uses **Entra ID** (`DefaultAzureCredential`) for token-based auth
- The app validates all required config at startup and fails fast with a clear message

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| AI Model | Azure OpenAI GPT-4o |
| Document Parsing | Azure AI Document Intelligence |
| Auth | Azure Entra ID (DefaultAzureCredential) |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Streaming | Server-Sent Events (SSE) |
| Deployment | Azure App Service + Gunicorn |

---

## 📄 License

This project is provided as a demonstration. See [LICENSE](LICENSE) for details.
