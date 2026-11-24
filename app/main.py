import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app import config, database
from app.llm import generate
from app.limiter import limiter

app = FastAPI(title="AI Business Assistant", version="1.0.0")
database.initialize()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

stats = {
    "requests": 0,
    "latency_total_ms": 0.0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "estimated_cost": 0.0,
}

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None

@app.get("/")
async def home():
    return FileResponse("app/static/index.html")

@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": config.LLM_MODE, "model": config.LLM_MODEL}

@app.get("/api/metrics")
async def metrics():
    count = stats["requests"]
    average_latency = round(stats["latency_total_ms"] / count, 2) if count else 0
    return {
        **stats,
        "average_latency_ms": average_latency,
        **database.counts(),
    }

@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")
    if len(message) > config.MAX_MESSAGE_CHARS:
        raise HTTPException(status_code=413, detail="Message is too long.")

    client_ip = request.client.host if request.client else "unknown"
    limiter.check(client_ip)

    conversation_id = body.conversation_id
    if conversation_id is None:
        conversation_id = database.create_conversation()

    database.add_message(conversation_id, "user", message)
    history = database.get_history(conversation_id, config.MAX_HISTORY_MESSAGES)

    started = time.perf_counter()
    try:
        result = await generate(history)
    except Exception as exc:
        # Do not expose provider credentials or internal stack traces.
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error: {type(exc).__name__}",
        )

    end_to_end_ms = round((time.perf_counter() - started) * 1000, 2)
    database.add_message(conversation_id, "assistant", result["answer"])

    stats["requests"] += 1
    stats["latency_total_ms"] += end_to_end_ms
    stats["prompt_tokens"] += result["prompt_tokens"]
    stats["completion_tokens"] += result["completion_tokens"]
    stats["estimated_cost"] += result["estimated_cost"]

    return {
        "conversation_id": conversation_id,
        **result,
        "end_to_end_latency_ms": end_to_end_ms,
    }
