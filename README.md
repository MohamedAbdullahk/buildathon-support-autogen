# 🤖 Multi-Agent Customer Support (AutoGen + FastAPI + Streamlit)

A production-style customer support system where **three AutoGen agents** work in sequence:

1. **Assistant**: answers from its own knowledge (no tools)
2. **Web Search Assistant**: searches the web (Serper) and answers from live results
3. **Entry Agent**: saves the query + both answers to `data/answers.txt` and returns both answers

Built for the **Gen AI Architect Program – Weekly Buildathon**, then restructured into a SaaS-ready layout.

---

## 🏗️ Architecture

```
User ─▶ Streamlit (frontend :8501)
            │  HTTP POST /api/v1/support
            ▼
        FastAPI (backend :8000)
            │
            ├─▶ Guardrails (input check) ── blocked? ─▶ return early (no LLM cost)
            │
            ├─▶ AutoGen RoundRobinGroupChat
            │      Assistant ─▶ Web_Search_Assistant ─▶ Entry_Agent
            │                        │                      │
            │                   web_search (Serper)    save_to_file
            │
            └─▶ Guardrails (output redaction) ─▶ JSON response
```

## ✨ Features

- **Sequential multi-agent team** (AutoGen `RoundRobinGroupChat` + termination conditions)
- **Fresh team per request**: no shared history between users
- **Guardrails**: prompt-injection / jailbreak blocking, length limits, API-key redaction
- **FastAPI backend** with Swagger docs (`/docs`) and health check (`/health`)
- **Streamlit frontend** that talks to the API only (no keys in the frontend)
- **Structured logging** with rotating log files
- **Tests**: fast unit tests (pytest) + LLM quality evals (DeepEval: Relevancy + Faithfulness)
- **Docker + docker-compose** with health checks, volumes and restart policies

## 📁 Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings from .env (pydantic-settings)
│   ├── agents/support_team.py  # 3 agents + team factory
│   ├── tools/                  # web_search.py, file_store.py
│   ├── services/               # support_service.py, guardrails.py
│   ├── routes/                 # health.py, support.py
│   └── utils/logger.py
├── frontend/
│   ├── app.py                  # Streamlit UI
│   └── requirements.txt
├── tests/
│   ├── test_guardrails.py      # free, fast unit tests
│   ├── test_eval_deepeval.py   # paid LLM evals (marker: eval)
│   └── smoke_*.py              # manual smoke tests
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt            # production dependencies
├── requirements-dev.txt        # + pytest, deepeval
├── pytest.ini
└── .env.example
```

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your keys:

```
OPENAI_API_KEY=your-openai-key-here
SERPER_API_KEY=your-serper-key-here
LLM_MODEL=gpt-4.1-mini
DATA_DIR=./data
LOG_DIR=./logs
BACKEND_URL=http://localhost:8000
```

> 🔒 Never commit `.env`. It is listed in `.gitignore` and `.dockerignore`.

## 🐳 Run with Docker (recommended)

```bash
docker compose up --build -d
docker compose ps          # both services should be (healthy)
```

| Service  | URL                            |
|----------|--------------------------------|
| Frontend | http://localhost:8502          |
| Backend  | http://localhost:8001/health   |
| API docs | http://localhost:8001/docs     |

Stop: `docker compose down`. Answers and logs persist in `./data` and `./logs`.

## 🐍 Run locally (without Docker)

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements-dev.txt

python -m backend.main                  # terminal 1 → http://localhost:8000
streamlit run frontend/app.py           # terminal 2 → http://localhost:8501
```

## 🧪 Tests

```bash
python -m pytest -v            # fast guardrail tests (free)
python -m pytest -m eval -v    # DeepEval quality tests (uses OpenAI credits)
```

## 🔌 API

`POST /api/v1/support`

```json
{ "query": "How do I reset my password?" }
```

Returns `assistant_answer`, `web_answer`, `blocked`, `block_reason`, `duration_seconds` and a full agent `trace`.

## 🛠️ Tech Stack

Python 3.11 · AutoGen AgentChat 0.7 · OpenAI `gpt-4.1-mini` · Serper · FastAPI · Streamlit · pytest · DeepEval · Docker