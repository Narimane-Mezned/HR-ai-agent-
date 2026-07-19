
import time
from openai import OpenAI, RateLimitError, APIStatusError, APITimeoutError, APIConnectionError


from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL_CHEAP
from app.db.call_logs import log_call

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

PRICING_PER_MILLION_TOKENS = {
    "openai/gpt-oss-20b:free": {"input": 0.0, "output": 0.0},
    "meta-llama/llama-3.3-70b-instruct:free": {"input": 0.0, "output": 0.0},
    "openrouter/free": {"input": 0.0, "output": 0.0},
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = PRICING_PER_MILLION_TOKENS.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def call_llm(system_prompt: str, user_prompt: str, model: str = OPENROUTER_MODEL_CHEAP, temperature: float = 0.2, max_tokens: int = 1500, max_retries: int = 3) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error = None

    for attempt in range(max_retries):
        try:
            start_time = time.time()

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning": {"exclude": True}},
            )

            latency_ms = round((time.time() - start_time) * 1000)

            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            cost = _estimate_cost(model, prompt_tokens, completion_tokens)

            log_call(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                estimated_cost=cost,
                latency_ms=latency_ms,
            )

            return response.choices[0].message.content

        except (RateLimitError, APIStatusError, APITimeoutError, APIConnectionError) as e:
            last_error = e
            wait_seconds = 15 * (attempt + 1)  # 15s, 30s, 45s — increasing backoff
            print(f"DEBUG: call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_seconds}s...")
            if attempt < max_retries - 1:
                time.sleep(wait_seconds)

   
    print(f"DEBUG: all {max_retries} attempts failed. Last error: {last_error}")
    return None