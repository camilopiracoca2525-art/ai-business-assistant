# LLM Observability Gateway

A small gateway that routes prompts to different model profiles and records operational metrics. It demonstrates practical trade-offs in model choice, request limits, fallback behavior, token accounting, latency and estimated cost.

## Capabilities

- Task-aware routing: `simple` tasks use the economy profile; `complex` tasks use the quality profile.
- OpenAI-compatible Chat Completions API integration.
- Optional fallback to the alternate configured model when the primary call fails.
- Mock mode for local testing without an API key.
- Per-client in-memory rate limiting.
- Prompt/completion token usage reporting.
- Configurable input/output price rates and estimated cost.
- In-memory metrics grouped by selected model.

## Run on Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn gateway.main:app --reload
```

Run from this project directory. Open http://127.0.0.1:8000/docs.

## Tests

```powershell
pytest -q
```

## Configure a real provider

Set `LLM_MODE=api`, `LLM_API_KEY`, and `LLM_BASE_URL` in `.env`. Set `MODEL_ECONOMY` and `MODEL_QUALITY` to model identifiers supported by your provider. Configure their input/output prices per one million tokens using the matching environment variables. The default rates are zero to avoid assuming current provider prices.

## API

- `GET /api/health`
- `POST /api/chat`
- `GET /api/metrics`

Example request:

```json
{
  "message": "Classify this support ticket and suggest a short next step.",
  "task": "simple"
}
```

Set `task` to `complex` to request the quality profile.

## Engineering trade-offs

| Concern | Approach | Trade-off |
|---|---|---|
| Model selection | Two environment-configurable profiles | Makes cost/quality choices explicit; requires task evaluation |
| Fallback | Try alternate profile after primary failure | Improves resilience but can add latency and cost |
| Rate limiting | In-memory per-client sliding window | Easy local demo; not distributed across workers |
| Token counts | Provider usage when available, rough estimate otherwise | Mock/estimate values are not tokenizer-grade |
| Cost | Configured provider rates x usage | Correct only if rates match provider's current published prices |
| Metrics | In-memory aggregates | Resets on restart; production needs durable telemetry |

This is a portfolio prototype, not a production gateway. Production hardening should include authentication, shared rate limiting, durable metrics, structured logging, secrets management, request/response redaction, budget enforcement, evaluations and load testing.
