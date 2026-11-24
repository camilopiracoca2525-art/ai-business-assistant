import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from automation.service import WorkflowService

service = WorkflowService(
    database_path=os.getenv("DATABASE_PATH", "./automation.db"),
    webhook_url=os.getenv("WEBHOOK_URL", ""),
    max_attempts=int(os.getenv("MAX_DELIVERY_ATTEMPTS", "3")),
    retry_delay_seconds=float(os.getenv("RETRY_DELAY_SECONDS", "0.2")),
)

app = FastAPI(title="Intelligent Workflow Automation", version="1.0.0")

class WorkflowRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=40)
    request_text: str = Field(min_length=1, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=120)

@app.get("/api/health")
def health():
    return {"status": "ok", "delivery_mode": "webhook" if service.webhook_url else "simulated"}

@app.post("/api/workflows/run")
def run_workflow(body: WorkflowRequest):
    try:
        return service.run(body.customer_id, body.request_text, body.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/api/workflows/runs")
def recent_runs(limit: int = 20):
    return {"runs": service.recent_runs(limit)}
