# 🔍 Expert-Level Issue Scout — Full Documentation

> An autonomous Python agent that monitors high-value GitHub repositories, uses Google Gemini AI to classify issues by technical complexity, and delivers real-time Telegram notifications for expert-level opportunities.

---

## 📁 Project Architecture

```
AI-opensource/
├── scout.py          # Main orchestrator — the brain of the system
├── ai_engine.py      # Gemini AI integration via REST API
├── github_client.py  # GitHub issue fetcher using PyGithub
├── storage.py        # SQLite memory to avoid duplicate processing
├── notifier.py       # Telegram notification sender
├── models.py         # Pydantic data models (type safety)
├── requirements.txt  # Python dependencies
├── run.bat           # One-click execution script (Windows)
├── .env              # API keys and secrets (not committed)
├── .env.example      # Template for .env
└── scout.db          # Auto-generated SQLite database (runtime)
```

---

## 🧩 File-by-File Breakdown

---

### 1. `models.py` — Data Models

**Purpose**: Defines the structured data types used across the entire project. Every other module imports from here.

**Why it exists**: Without strict types, data would be passed around as raw dictionaries, leading to typos, missing fields, and hard-to-debug errors. Pydantic enforces type safety at runtime.

```python
from pydantic import BaseModel, Field
from typing import List, Optional
```

#### Classes

| Class | Fields | Purpose |
|-------|--------|---------|
| `GitHubIssue` | `id`, `number`, `title`, `body`, `html_url`, `repo_name` | Represents a single GitHub issue fetched from the API |
| `IssueAnalysis` | `fit_score`, `is_expert_level`, `implementation_strategy`, `reasoning` | Represents the AI's verdict on an issue |

#### Key Design Decisions
- **`fit_score: int = Field(ge=1, le=10)`** — Pydantic's `Field` with `ge` (greater/equal) and `le` (less/equal) constraints ensures the AI never returns a score outside 1-10.
- **`body: Optional[str] = ""`** — Some GitHub issues have no body. This default prevents `NoneType` errors downstream.
- **`BaseModel`** — Pydantic's base class. Any class inheriting from it gets automatic JSON serialization, validation, and type coercion.

#### Libraries Used
| Library | Import | Use Case |
|---------|--------|----------|
| `pydantic` | `BaseModel`, `Field` | Runtime data validation. When we do `IssueAnalysis(**data)`, Pydantic validates every field type and constraint automatically. |
| `typing` | `List`, `Optional` | Python type hints for better IDE support and code clarity. |

---

### 2. `github_client.py` — GitHub Issue Fetcher

**Purpose**: Connects to the GitHub API and fetches the most recent open issues from any repository, filtering out Pull Requests.

**Why it exists**: GitHub's API is complex (pagination, rate limits, authentication). PyGithub abstracts all of this into simple Python objects.

```python
import os
from github import Github
from models import GitHubIssue
from typing import List
from dotenv import load_dotenv
```

#### How It Works
1. **`__init__`**: Reads `GITHUB_TOKEN` from `.env` and creates an authenticated GitHub client.
2. **`fetch_recent_issues(repo_full_name, limit=10)`**:
   - Calls `repo.get_issues(state='open', sort='created', direction='desc')` — gets open issues sorted newest first.
   - **Skips Pull Requests**: GitHub's API returns PRs mixed with issues. The `issue.pull_request` check filters them out.
   - **Respects the `limit`**: Stops after collecting `limit` real issues (not PRs).
   - Returns a list of `GitHubIssue` Pydantic models.

#### Key Design Decisions
- **Lazy iteration**: PyGithub returns a `PaginatedList` (lazy iterator). We iterate and break early — this avoids fetching all 10,000+ issues from large repos like `pytorch`.
- **No `len()` on PaginatedList**: Calling `len()` would force-fetch ALL pages. This was a bug I fixed during development.

#### Libraries Used
| Library | Import | Use Case |
|---------|--------|----------|
| `PyGithub` | `Github` | Full-featured GitHub API wrapper. Handles OAuth, pagination, rate limiting, and object mapping. |
| `python-dotenv` | `load_dotenv` | Loads `.env` file into `os.environ` so we can read `GITHUB_TOKEN`. |
| `os` | `os.getenv` | Reads environment variables. |

---

### 3. `ai_engine.py` — Gemini AI Analysis Engine

**Purpose**: Takes a GitHub issue and uses Google's Gemini 2.5 Flash model to determine if it's "expert-level" — scoring it 1-10 and providing an implementation strategy.

**Why it exists**: The core intelligence of the system. Without AI, we'd need manual rules that can't understand the nuance of technical issues.

```python
import os
import requests
import json
from models import GitHubIssue, IssueAnalysis
from dotenv import load_dotenv
import re
```

#### How It Works
1. **`__init__`**: Reads `GEMINI_API_KEY` from `.env`. Constructs the REST API URL for `gemini-2.5-flash`.
2. **`analyze_issue(issue)`**:
   - Builds a detailed **prompt** that instructs Gemini to act as a "Lead AI Engineer".
   - Sends a **POST request** to `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`.
   - Uses **JSON mode** (`response_mime_type: "application/json"`) to force structured output.
   - Parses the response and returns an `IssueAnalysis` Pydantic model.
   - **Fallback**: If JSON parsing fails, uses regex (`re.search`) to extract JSON from freeform text.
   - **Error handling**: Returns a safe default (`fit_score=1, is_expert_level=False`) with "AI Error" in reasoning.

#### Why REST Instead of the SDK?
The `google-generativeai` Python SDK caused issues:
- **Interactive prompts**: The SDK's gRPC transport triggered `(Y/N)?` prompts that blocked autonomous execution.
- **Model naming inconsistencies**: The SDK couldn't resolve `gemini-1.5-flash` vs `models/gemini-1.5-flash`.
- **Direct REST** is simpler, more predictable, and has zero dependencies beyond `requests`.

#### The Prompt Engineering
The prompt uses a structured approach:
- **Role definition**: "You are a Lead AI Engineer"
- **Positive criteria**: RAG, multi-agent, PyTorch/TensorFlow, complex React state
- **Negative criteria**: Documentation typos, CSS fixes, basic feature requests
- **Output schema**: Exact JSON format with field descriptions
- **Body truncation**: `issue.body[:3000]` prevents exceeding Gemini's context window

#### Libraries Used
| Library | Import | Use Case |
|---------|--------|----------|
| `requests` | `requests.post` | HTTP client for making REST API calls to Gemini. Lightweight, no gRPC dependency. |
| `json` | `json.loads` | Parsing the JSON response from Gemini into a Python dictionary. |
| `re` | `re.search` | Regex fallback to extract JSON from Gemini responses that aren't perfectly formatted. |
| `python-dotenv` | `load_dotenv` | Loads `GEMINI_API_KEY` from `.env`. |

---

### 4. `storage.py` — SQLite Memory System

**Purpose**: Tracks which issues have already been processed so the scout never analyzes the same issue twice across runs.

**Why it exists**: Without persistence, every hourly cycle would re-analyze all 140+ issues (20 per repo × 7 repos), wasting API calls and sending duplicate notifications.

```python
import sqlite3
import os
```

#### How It Works
1. **`__init__`**: Creates/opens `scout.db` and ensures the `processed_issues` table exists.
2. **`is_processed(issue_id)`**: Checks if an issue ID exists in the database.
3. **`mark_processed(issue_id)`**: Inserts the issue ID. Uses `INSERT OR IGNORE` to handle duplicates gracefully.

#### Database Schema
```sql
CREATE TABLE IF NOT EXISTS processed_issues (
    issue_id INTEGER PRIMARY KEY
);
```

#### Key Design Decisions
- **SQLite**: Zero-configuration, serverless, file-based. Perfect for a single-user tool — no PostgreSQL/MySQL setup needed.
- **Connection-per-call**: Each method opens and closes its own connection. This avoids stale connections and is thread-safe.
- **`INSERT OR IGNORE`**: If somehow the same issue ID is inserted twice, SQLite silently ignores it instead of crashing.
- **Critical flaw fix**: Issues are only marked as processed when the AI analysis **succeeds**. If Gemini returns an error, the issue stays unprocessed and gets retried next cycle.

#### Libraries Used
| Library | Import | Use Case |
|---------|--------|----------|
| `sqlite3` | Built-in | Python's built-in SQLite interface. No installation needed. Creates a `scout.db` file in the project root. |

---

### 5. `notifier.py` — Telegram Notification System

**Purpose**: Sends beautifully formatted notifications to a Telegram chat when an expert-level issue is found.

**Why it exists**: The whole point of the scout is to alert you in real-time. Telegram is instant, free, and works on mobile.

```python
import os
import requests
from models import GitHubIssue, IssueAnalysis
from dotenv import load_dotenv
```

#### How It Works
1. **`__init__`**: Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from `.env`.
2. **`notify(issue, analysis)`**:
   - Constructs an HTML-formatted message with emojis, bold text, and a clickable link to the issue.
   - If Telegram credentials are missing, falls back to **console printing** (for testing without a bot).
   - Sends via `POST` to `https://api.telegram.org/bot{token}/sendMessage` with `parse_mode: "HTML"`.

#### Message Format
```
🚀 New Expert Issue Found!

📍 Repo: langchain-ai/langgraph
🔗 Issue: [Bug] RAG context lost in multi-agent streaming

📊 Fit Score: 9/10
💡 Strategy: Fix context serialization in agent handoff protocol

🧐 Reasoning: RAG + multi-agent coordination = core expert domains
```

#### Why HTML Instead of Markdown?
Telegram's Markdown parser is strict — characters like `_`, `*`, `[`, `]` in issue titles would crash the message. HTML mode (`<b>`, `<a href>`) is far more forgiving and never fails on special characters.

#### Libraries Used
| Library | Import | Use Case |
|---------|--------|----------|
| `requests` | `requests.post` | Sends HTTP POST to the Telegram Bot API. |
| `python-dotenv` | `load_dotenv` | Loads bot token and chat ID from `.env`. |

---

### 6. `scout.py` — Main Orchestrator

**Purpose**: The entry point and brain of the entire system. Ties all modules together into a continuous monitoring loop.

**Why it exists**: Each module is independent. The orchestrator defines the workflow: fetch → analyze → decide → notify → sleep → repeat.

```python
import os, sys, time, warnings
from dotenv import load_dotenv
from github_client import GitHubClient
from ai_engine import AIEngine
from storage import Storage
from notifier import TelegramNotifier
```

#### How It Works
1. **Initialization**: Creates instances of all four modules.
2. **Repository loop**: Iterates over the `REPOS` list.
3. **Issue loop**: For each repo, fetches 20 recent issues.
4. **Processing pipeline** for each issue:
   - Skip if already in `scout.db`
   - Send to Gemini for analysis
   - If `is_expert_level == True` → send Telegram notification
   - If analysis succeeded → mark as processed
   - If analysis failed (AI Error) → skip (will retry next cycle)
   - Sleep 1 second between API calls (rate limiting)
5. **Continuous mode**: When run without `--test`, loops forever with 1-hour sleep between cycles.

#### Monitored Repositories
| Repository | Domain |
|------------|--------|
| `langchain-ai/langgraph` | Multi-agent AI orchestration |
| `crewAIInc/crewAI` | AI agent frameworks |
| `pytorch/pytorch` | Deep learning framework |
| `google-gemini/cookbook` | Gemini AI examples |
| `n8n-io/n8n` | Workflow automation |
| `aden-hive/hive` | Collaborative platform |
| `calcom/cal.com` | Scheduling infrastructure |

#### Key Design Decisions
- **`warnings.filterwarnings("ignore")`**: Suppresses deprecation warnings from libraries for clean output.
- **`--test` flag**: Runs a single cycle on `langchain-ai/langchain` only. Used for debugging.
- **Graceful error handling**: If one repo fails (404, network error), the scout continues to the next repo.
- **1-second delay**: Prevents hitting Gemini's rate limit (especially on free tier).

#### Libraries Used
| Library | Import | Use Case |
|---------|--------|----------|
| `sys` | `sys.argv` | Command-line argument parsing (`--test` flag). |
| `time` | `time.sleep` | Rate limiting between API calls and the 1-hour cycle sleep. |
| `warnings` | `warnings.filterwarnings` | Suppresses noisy library warnings. |

---

### 7. `run.bat` — One-Click Execution Script

**Purpose**: Windows batch script that handles virtual environment activation and runs the scout in one click.

```batch
@echo off
if not exist venv (
    python -m venv venv
    .\venv\Scripts\python -m pip install -r requirements.txt
)
echo Y | .\venv\Scripts\python scout.py %*
pause
```

#### What It Does
1. Creates the `venv` if it doesn't exist.
2. Installs all dependencies from `requirements.txt`.
3. Runs `scout.py` with any arguments passed (e.g., `--test`).
4. `echo Y |` pipes "Y" to stdin to bypass any interactive prompts from libraries.
5. `pause` keeps the window open so you can read the output.

---

### 8. `requirements.txt` — Dependencies

```
PyGithub
google-generativeai
python-dotenv
pydantic
requests
tqdm
```

---

### 9. `.env` — Secrets Configuration

```env
GITHUB_TOKEN=ghp_xxxx          # GitHub Personal Access Token
GEMINI_API_KEY=AIzaSyXxxxx      # Google AI Studio API Key
TELEGRAM_BOT_TOKEN=123456:ABCx  # Telegram Bot Token from @BotFather
TELEGRAM_CHAT_ID=7069295447     # Your Telegram numeric chat ID
```

---

## 🛠️ Complete Tech Stack

### Core Language
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python 3.x** | 3.10+ | Primary language. Chosen for its rich ecosystem of AI/API libraries. |

### Libraries

| Library | Version | Used In | Purpose |
|---------|---------|---------|---------|
| **PyGithub** | Latest | `github_client.py` | Full GitHub API v3 wrapper. Handles authentication, pagination, rate limiting, and maps API responses to Python objects. |
| **requests** | Latest | `ai_engine.py`, `notifier.py` | HTTP client for REST API calls (Gemini AI, Telegram Bot API). Lightweight alternative to `aiohttp`/`httpx`. |
| **pydantic** | v2 | `models.py` | Data validation and serialization. Ensures all data flowing through the system is correctly typed and constrained. |
| **python-dotenv** | Latest | All modules | Loads `.env` file into environment variables. Keeps secrets out of source code. |
| **sqlite3** | Built-in | `storage.py` | Embedded SQL database. Zero-config, serverless, file-based. Ships with Python. |
| **google-generativeai** | Latest | `requirements.txt` | Installed but **not actively used** — we switched to direct REST calls for reliability. Kept in requirements for potential future use. |
| **tqdm** | Latest | `requirements.txt` | Progress bar library. Available for future improvements (e.g., showing progress during batch analysis). |

### External APIs

| API | Endpoint | Auth Method | Purpose |
|-----|----------|-------------|---------|
| **GitHub REST API v3** | `api.github.com` | Personal Access Token (Bearer) | Fetching repository issues, filtering PRs, reading issue metadata. |
| **Google Gemini API** | `generativelanguage.googleapis.com/v1beta` | API Key (query param) | AI-powered issue classification using `gemini-2.5-flash` model. |
| **Telegram Bot API** | `api.telegram.org` | Bot Token (URL path) | Sending formatted HTML notifications to a Telegram chat. |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | SQLite (`scout.db`) | Persistence layer to track processed issues across restarts. |
| **Environment** | Python venv | Isolated dependency management. |
| **Execution** | Windows Batch (`run.bat`) | One-click startup with auto-setup. |

---

## 🔄 Data Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   GitHub     │────►│  github_client   │────►│   models    │
│   API        │     │  (PyGithub)      │     │  (Pydantic) │
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
                                                     ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   SQLite     │◄───│    storage        │◄───│    scout     │
│   (scout.db) │    │    (sqlite3)      │    │  (orchestrator)│
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
                                                     ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Gemini     │◄───│   ai_engine      │◄───│  IssueAnalysis│
│   API        │    │   (REST/HTTP)    │────►│  (Pydantic)  │
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
                                                     ▼
┌─────────────┐     ┌──────────────────┐            │
│  Telegram   │◄───│    notifier       │◄───────────┘
│  Bot API    │    │    (requests)     │  (if expert-level)
└─────────────┘     └──────────────────┘
```

---

## 🚀 How to Run

```powershell
# Test mode (single repo, one cycle)
.\run.bat --test

# Production mode (all repos, continuous loop every 1 hour)
.\run.bat
```
