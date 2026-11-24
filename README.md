# AI Business Assistant

A portfolio project demonstrating how to connect an OpenAI-compatible language model API to a business-style application.

## Features
- FastAPI backend and browser chat interface
- Mock mode for a no-key demo, plus configurable real API mode
- SQLite conversation and message persistence
- Model and provider selection through environment variables
- Input validation and per-IP request rate limiting
- End-to-end latency measurement
- Prompt/completion token reporting and configurable cost estimates
- Basic automated tests

## Architecture

```text
Browser UI
   |
   v
FastAPI (/api/chat)
   |-- Input validation and rate limit
   |-- SQLite conversation history
   |-- LLM client (mock or OpenAI-compatible API)
   |-- Latency, token and estimated-cost telemetry
   v
JSON response and metrics
```

## Requirements
- Python 3.10+
- Optional API key for an OpenAI-compatible provider

## Run locally on Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Connect a real model

Edit `.env` and set:
- `LLM_MODE=api`
- `LLM_API_KEY` to your provider key
- `LLM_BASE_URL` to the provider API base URL
- `LLM_MODEL` to the model you want to evaluate

The provider must implement the OpenAI-compatible `POST /chat/completions` interface. Never commit a real API key. The default `mock` mode runs without a key and does not call an LLM.

## Cost configuration

Set `INPUT_COST_PER_1M` and `OUTPUT_COST_PER_1M` to the provider's current input/output prices per one million tokens. Defaults are zero so the application does not assume or publish potentially outdated prices. Estimates are only as accurate as the configured provider rates and usage data. Mock-mode token counts are rough character-based estimates, not tokenizer output.

## API

- `GET /api/health` — service status, mode and configured model
- `GET /api/metrics` — request, latency, token and estimated-cost totals
- `POST /api/chat` — submit a message

Example request:

```json
{
  "message": "Summarize the benefits of automating invoice intake.",
  "conversation_id": null
}
```

## Engineering trade-offs

| Concern | Current approach | Trade-off |
|---|---|---|
| Model selection | Configurable provider model through environment variables | Easy to switch models; quality and cost still need evaluation |
| Token use | Recent conversation window and bounded input | Controls context size; older context can be omitted |
| Latency | Measures the model call and end-to-end request | Simple baseline; streaming is not implemented yet |
| Rate limiting | In-memory per-IP sliding window | No infrastructure required; state is not shared across workers and resets on restart |
| Persistence | SQLite | Easy local setup; PostgreSQL is more suitable for concurrent production use |
| Cost | Usage multiplied by configured provider rates | Depends on accurate, current provider pricing |

## Tests

```bash
pytest -q
```

## Limitations and next steps

This is a learning/portfolio implementation, not a production-ready service. The next engineering steps are authentication, HTTPS, a shared rate-limit store such as Redis, streaming and cancellation, improved ownership checks for conversation IDs, structured logs, evaluation datasets, Docker, and CI.

## Author

Portfolio repository: `camilopiracoca2525-art`.
