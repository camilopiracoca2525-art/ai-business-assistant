import time
import httpx
from app import config

SYSTEM_PROMPT = (
    "You are a concise business assistant. Be accurate, state uncertainty, "
    "and never claim to have accessed company systems unless data is provided."
)

def estimate_tokens(text: str) -> int:
    # Rough character-based estimate for demo telemetry only, not a tokenizer.
    return max(1, (len(text) + 3) // 4) if text else 0

async def generate(messages: list[dict]) -> dict:
    started = time.perf_counter()
    prompt_estimate = estimate_tokens(" ".join(m["content"] for m in messages))

    if config.LLM_MODE != "api":
        last = messages[-1]["content"] if messages else ""
        answer = (
            "[MOCK MODE] I received: " + last[:500]
            + "\n\nThis is a simulated answer. Set LLM_MODE=api and configure an API key "
            "to call a real language model."
        )
        output_estimate = estimate_tokens(answer)
        return {
            "answer": answer,
            "model": "mock",
            "prompt_tokens": prompt_estimate,
            "completion_tokens": output_estimate,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "estimated_cost": 0.0,
        }

    if not config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is missing while LLM_MODE=api")

    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0)) as client:
        response = await client.post(
            f"{config.LLM_BASE_URL}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
        )
        response.raise_for_status()
        data = response.json()

    answer = data["choices"][0]["message"]["content"]
    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or prompt_estimate)
    completion_tokens = int(usage.get("completion_tokens") or estimate_tokens(answer))
    estimated_cost = (
        prompt_tokens * config.INPUT_COST_PER_1M
        + completion_tokens * config.OUTPUT_COST_PER_1M
    ) / 1_000_000

    return {
        "answer": answer,
        "model": data.get("model", config.LLM_MODEL),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "estimated_cost": round(estimated_cost, 8),
    }
