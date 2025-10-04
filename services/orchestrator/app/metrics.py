import time
from typing import Callable
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, CONTENT_TYPE_LATEST, generate_latest


# App metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "code"],
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency (seconds)",
    labelnames=["endpoint"],
)

# Domain Metrics
BATTLE_ROUNDS = Counter(
    "battle_rounds_total",
    "Total rounds processed across all battles",
)
BATTLE_BREACHES = Counter(
    "battle_breaches_total",
    "Total breaches across all battles",
)
BATTLE_ACTIVE = Gauge(
    "battle_active_runs",
    "Number of currently running battles",
)
BREACH_RATE = Gauge(
    "battle_breach_rate",
    "Current breach rate (last updated by runner)",
)

def metrics_endpoint():
    """Return a FastAPI handler for /metrics"""
    return lambda: Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def http_metrics_middleware(app_endpoint_namer: Callable[[Request], str]):
    """
    Returns a FastAPI middleware function that measures request count/latency.
    app_endpoint_namer: function(Request)->str that returns a small endpoint label (e.g., "/battle/start")
    """
    async def _middleware(request: Request, call_next):
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            endpoint = app_endpoint_namer(request)
            duration = time.perf_counter() - start
            code = str(response.status_code if response else 500)
            HTTP_REQUESTS.labels(request.method, endpoint, code).inc()
            HTTP_LATENCY.labels(endpoint).observe(duration)
    return _middleware
