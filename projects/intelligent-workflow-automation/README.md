# Intelligent Workflow Automation

An API-based workflow engine that demonstrates how to connect business processes to external systems reliably.

## Capabilities

- FastAPI endpoints to trigger workflows and inspect recent runs.
- A small mock CRM dataset so the project works locally without credentials.
- Idempotency keys to prevent duplicate processing on client retries.
- Step-by-step execution history persisted in SQLite.
- Configurable retry attempts for webhook delivery.
- Optional webhook adapter for connecting a real downstream system.
- Tests for successful execution, duplicate requests, validation and retries.

## Workflow

```text
API request
   |
   v
Validate request
   |
   v
Look up customer (mock CRM adapter)
   |
   v
Prepare business notification
   |
   v
Deliver
   |---- no webhook configured: simulate delivery
   |---- webhook configured: POST JSON with retries
   v
Persist run status and step events
```

## Run on Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn automation.main:app --reload
```

Run these commands from this project directory. Open http://127.0.0.1:8000/docs.

## Run tests

```powershell
pytest -q
```

## API

- `GET /api/health`
- `POST /api/workflows/run`
- `GET /api/workflows/runs`

Example:

```json
{
  "customer_id": "C-1001",
  "request_text": "Please send the updated service schedule.",
  "idempotency_key": "schedule-update-001"
}
```

## Configuration

- `DATABASE_PATH`: SQLite database file.
- `WEBHOOK_URL`: optional URL to receive completed workflow notifications.
- `MAX_DELIVERY_ATTEMPTS`: retry attempts for webhook delivery.
- `RETRY_DELAY_SECONDS`: base delay for exponential backoff.

When a webhook is configured, the app sends customer and message data to that URL. Use a trusted test endpoint and non-sensitive test data only.

## Engineering decisions and limitations

SQLite and a process-local service keep the demo easy to run. This is not a distributed workflow orchestrator: concurrent workers, durable queues, distributed locks, authentication, secret management, dead-letter queues and observability should be added before production use. Retry delays are intentionally configurable and should be tuned for a real downstream API.
