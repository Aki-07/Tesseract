"""
cerebras_adapter.py

Async-friendly adapter to call Cerebras inference. Uses the official SDK if available.
Requires only the CEREBRAS_API_KEY environment variable to be set.
"""

import os
import asyncio
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Try to import the official Cerebras SDK
try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_SDK_AVAILABLE = True
except ImportError:
    CEREBRAS_SDK_AVAILABLE = False
    logger.debug("Cerebras SDK not available, will use HTTP fallback")

# Configuration via environment
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_API_BASE = os.getenv("CEREBRAS_API_URL", "https://api.cerebras.ai/v1")
DEFAULT_MODEL = os.getenv("CEREBRAS_DEFAULT_MODEL", "llama-4-scout-17b-16e-instruct")
# Retry policy
_RETRY_STOP = stop_after_attempt(3)
_RETRY_WAIT = wait_exponential(multiplier=1, min=1, max=8)

def _ensure_key():
    if not CEREBRAS_API_KEY:
        raise RuntimeError("CEREBRAS_API_KEY is not set in the environment")

@retry(stop=_RETRY_STOP, wait=_RETRY_WAIT, reraise=True)
def _sync_sdk_call(prompt: str, model: str, max_tokens: int, temperature: float) -> str:
    """
    Perform synchronous call via the Cerebras SDK.
    """
    if not CEREBRAS_SDK_AVAILABLE:
        raise RuntimeError("Cerebras SDK not installed")

    client = Cerebras(api_key=CEREBRAS_API_KEY)
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_completion_tokens=max_tokens,
        temperature=temperature,
        stream=False,
    )
    
    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content or ""
    return ""

async def _httpx_call(prompt: str, model: str, max_tokens: int, temperature: float, timeout: float = 30.0) -> str:
    """
    Async HTTP call to Cerebras chat/completions REST endpoint.
    """
    _ensure_key()
    url = f"{CEREBRAS_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract text from response
        if "choices" in data and data["choices"]:
            return data["choices"][0].get("message", {}).get("content", "") or ""
        return ""

async def call_cerebras(
    prompt: str, 
    model: Optional[str] = None, 
    max_tokens: int = 256, 
    temperature: float = 0.2
) -> str:
    """
    Public async entrypoint. Returns text produced by Cerebras.
    """
    _ensure_key()
    model = model or DEFAULT_MODEL

    # Try SDK if available
    if CEREBRAS_SDK_AVAILABLE:
        try:
            logger.debug("cerebras_adapter: calling via SDK", extra={"model": model})
            resp = await asyncio.to_thread(_sync_sdk_call, prompt, model, max_tokens, temperature)
            logger.info("cerebras_adapter.sdk_success", extra={"model": model, "out_len": len(resp)})
            return resp
        except Exception as e:
            logger.warning("cerebras_adapter.sdk_failed_falling_back_to_http: %s", e)

    # Fallback to HTTP API
    try:
        logger.debug("cerebras_adapter: calling via REST HTTP", extra={"model": model})
        text = await _httpx_call(prompt, model, max_tokens, temperature)
        logger.info("cerebras_adapter.http_success", extra={"model": model, "out_len": len(text)})
        return text
    except Exception as e:
        logger.exception("cerebras_adapter.http_failed: %s", e)
        raise