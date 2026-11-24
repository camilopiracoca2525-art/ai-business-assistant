# AI Business Assistant

Portfolio project: connect an OpenAI-compatible LLM API to a business-style assistant.

## Features
- FastAPI backend and browser chat UI
- Mock mode (runs without an API key) and real API mode
- SQLite conversation history
- Configurable model and provider URL
- Request rate limiting, input-size validation and latency measurement
- Token usage and estimated cost dashboard

## Run on Windows
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

## Connect a real model
Edit `.env` and set `LLM_MODE=api`, `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`.
The provider must support the OpenAI-compatible `/chat/completions` endpoint.
Never commit API keys. The default mock mode works without a key.

## Tests
```bash
pytest -q
```

## Engineering trade-offs
| Area | Implementation | Trade-off |
|---|---|---|
| Model choice | Environment-configurable model | Easy switching; quality/cost must be evaluated |
| Context | Bounded recent message history | Lower token use; older context can be omitted |
| Latency | End-to-end provider call timing | Simple baseline; no streaming yet |
| Rate limit | In-memory per-IP window | No infrastructure; not shared across workers |
| Storage | SQLite | Easy local setup; PostgreSQL suits production |
| Cost | Provider usage x configured price | Accurate only when pricing is configured correctly |

This is a learning/portfolio demo, not a production-ready service. Production needs authentication, HTTPS, shared rate limiting (e.g. Redis), stronger monitoring, and deployment hardening.
