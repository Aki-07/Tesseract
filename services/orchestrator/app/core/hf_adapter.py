import os
import logging
from typing import Optional, Dict, Any, Union
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

HF_API_URL = "https://api-inference.huggingface.co/models"


class HuggingFaceAdapter:
    """
    Adapter for Hugging Face Inference API.

    Supports text generation models with automatic retries,
    proper error handling, and response parsing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        Initialize the Hugging Face adapter.

        Args:
            api_key: HF API token. If None, reads from HF_API_KEY env var
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts on failure
        """
        self.api_key = api_key or os.getenv("HF_API_KEY")
        if not self.api_key:
            raise ValueError(
                "HF_API_KEY must be provided or set as environment variable"
            )

        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def call_model(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.95,
        do_sample: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        Call a Hugging Face model for text generation.

        Args:
            model_id: HF model identifier (e.g., "gpt2", "meta-llama/Llama-2-7b-hf")
            prompt: Input text prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling threshold
            do_sample: Whether to use sampling or greedy decoding
            **kwargs: Additional model-specific parameters

        Returns:
            Generated text string

        Raises:
            httpx.HTTPStatusError: On API errors (401, 429, 500, etc.)
            httpx.TimeoutException: On request timeout
            ValueError: On invalid response format
        """
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": do_sample,
                "return_full_text": False,  # Only return generated text
                **kwargs,
            },
        }

        logger.info(f"Calling HF model: {model_id} with prompt length: {len(prompt)}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    f"{HF_API_URL}/{model_id}",
                    headers=self.headers,
                    json=payload,
                )
                resp.raise_for_status()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid HF API key") from e
                elif e.response.status_code == 429:
                    logger.warning("Rate limited by HF API, retrying...")
                    raise
                elif e.response.status_code == 503:
                    logger.warning(f"Model {model_id} is loading, retrying...")
                    raise
                else:
                    logger.error(
                        f"HF API error: {e.response.status_code} - {e.response.text}"
                    )
                    raise

            return self._parse_response(resp.json())

    def _parse_response(self, data: Union[Dict, list, str]) -> str:
        """
        Parse HF API response into a string.

        Different models return different formats:
        - List of dicts: [{"generated_text": "..."}]
        - Dict: {"generated_text": "..."}
        - String: "..."
        """
        if isinstance(data, list):
            if not data:
                raise ValueError("Empty response from HF API")

            first_item = data[0]
            if isinstance(first_item, dict):
                return first_item.get("generated_text", "")
            return str(first_item)

        elif isinstance(data, dict):
            if "error" in data:
                raise ValueError(f"HF API error: {data['error']}")

            return data.get("generated_text", str(data))

        elif isinstance(data, str):
            return data

        else:
            logger.warning(f"Unexpected response type: {type(data)}")
            return str(data)

    async def check_model_status(self, model_id: str) -> Dict[str, Any]:
        """
        Check if a model is loaded and ready.

        Args:
            model_id: HF model identifier

        Returns:
            Status dictionary with 'loaded' and 'estimated_time' keys
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{HF_API_URL}/{model_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def stream_model(
        self,
        model_id: str,
        prompt: str,
        max_new_tokens: int = 256,
        **kwargs: Any,
    ):
        """
        Stream tokens from a model (if supported).

        Args:
            model_id: HF model identifier
            prompt: Input prompt
            max_new_tokens: Max tokens to generate
            **kwargs: Additional parameters

        Yields:
            Generated text chunks
        """
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "return_full_text": False,
                **kwargs,
            },
            "options": {"use_cache": False},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{HF_API_URL}/{model_id}",
                headers=self.headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_text():
                    if chunk.strip():
                        yield chunk


async def call_hf_model(model_id: str, prompt: str, **kwargs) -> str:
    """
    Simple function interface for calling HF models.

    Args:
        model_id: HF model identifier
        prompt: Input prompt
        **kwargs: Additional parameters

    Returns:
        Generated text
    """
    adapter = HuggingFaceAdapter()
    return await adapter.call_model(model_id, prompt, **kwargs)


async def call_cerebras():
    pass
