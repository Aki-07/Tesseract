import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.orchestrator.app.metrics import (
    CONTENT_TYPE_LATEST,
    HTTP_LATENCY,
    HTTP_REQUESTS,
    http_metrics_middleware,
    metrics_endpoint,
)


def _sample_value(metric, sample_name, labels):
    for collected in metric.collect():
        for sample in collected.samples:
            if sample.name == sample_name and sample.labels == labels:
                return sample.value
    return 0.0


def test_metrics_endpoint_returns_prometheus_payload():
    handler = metrics_endpoint()
    response = handler()

    assert response.media_type == CONTENT_TYPE_LATEST
    assert response.body.startswith(b"# HELP")


def test_http_metrics_middleware_records_requests_and_latency():
    app = FastAPI()
    app.middleware("http")(http_metrics_middleware(lambda req: req.url.path))

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)

    labels_req = {"method": "GET", "endpoint": "/ping", "code": "200"}
    before_requests = _sample_value(HTTP_REQUESTS, "http_requests_total", labels_req)
    before_latency = _sample_value(HTTP_LATENCY, "http_request_duration_seconds_count", {"endpoint": "/ping"})

    response = client.get("/ping")

    assert response.status_code == 200

    after_requests = _sample_value(HTTP_REQUESTS, "http_requests_total", labels_req)
    after_latency = _sample_value(HTTP_LATENCY, "http_request_duration_seconds_count", {"endpoint": "/ping"})

    assert after_requests == pytest.approx(before_requests + 1)
    assert after_latency == pytest.approx(before_latency + 1)
