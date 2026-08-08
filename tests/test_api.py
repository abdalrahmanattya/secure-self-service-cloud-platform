import json

import pytest
from fastapi.testclient import TestClient

from secure_cloud_platform.api import create_app
from secure_cloud_platform.service import PlatformService
from test_service import make_request


@pytest.mark.parametrize(
    ("provider", "region"),
    [("aws", "eu-west-1"), ("azure", "northeurope")],
)
def test_api_uses_real_provider_adapters_and_returns_identity(
    provider: str, region: str
) -> None:
    service = PlatformService()
    client = TestClient(create_app(service))
    setup = client.post("/v1/platform/installations", json={"provider": provider})
    assert setup.status_code == 201
    body = make_request(region=region).model_dump(mode="json")
    response = client.post(
        "/v1/environment-requests",
        json=body,
        headers={"Idempotency-Key": "api-key"},
    )
    assert response.status_code == 200
    request_id = response.json()["request"]["request_id"]
    direct = service.get_environment_request(request_id)
    assert request_id == direct.request.request_id
    assert response.json()["outcome"]["decision"] == direct.outcome.decision.model_dump(
        mode="json"
    )


def test_api_idempotency_404_409_list_and_denied_record() -> None:
    service = PlatformService()
    client = TestClient(create_app(service))
    client.post("/v1/platform/installations", json={"provider": "aws"})
    body = make_request().model_dump(mode="json")
    assert client.post("/v1/environment-requests", json=body).status_code == 400
    first = client.post(
        "/v1/environment-requests",
        json=body,
        headers={"Idempotency-Key": "one"},
    )
    assert first.status_code == 200
    conflict = client.post(
        "/v1/environment-requests",
        json={**body, "application": "other"},
        headers={"Idempotency-Key": "one"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency-conflict"
    denied = client.post(
        "/v1/environment-requests",
        json={**body, "network_cidr": "8.8.8.0/24"},
        headers={"Idempotency-Key": "denied"},
    )
    assert denied.status_code == 200
    request_id = denied.json()["request"]["request_id"]
    assert denied.json()["state"] == "denied"
    assert client.get(f"/v1/environment-requests/{request_id}").status_code == 200
    assert len(client.get("/v1/environment-requests").json()["requests"]) == 2
    assert client.get("/v1/environment-requests/env-doesnotexist").status_code == 404


def test_api_health_version_metrics_and_malformed_input() -> None:
    client = TestClient(create_app(PlatformService()))
    assert client.get("/health").json() == {"status": "ok", "simulation": True}
    assert client.get("/version").json()["name"] == (
        "secure-self-service-cloud-platform"
    )
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "platform_environment_requests_total 0" in metrics.text
    malformed = client.post(
        "/v1/environment-requests",
        json={"application": "missing-fields"},
        headers={"Idempotency-Key": "malformed"},
    )
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "validation-error"


def test_rejected_setup_is_structured_and_retryable() -> None:
    service = PlatformService()
    client = TestClient(create_app(service))
    rejected = client.post(
        "/v1/platform/installations",
        json={
            "provider": "aws",
            "guardrails": {"allowed_regions": ["northeurope"]},
        },
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "installation-rejected"
    assert rejected.json()["error"]["fields"][0]["field"] == (
        "guardrails.allowed_regions"
    )
    retry = client.post("/v1/platform/installations", json={"provider": "azure"})
    assert retry.status_code == 201


def test_api_has_no_apply_plan_or_destroy_endpoint() -> None:
    paths = {route.path for route in create_app(PlatformService()).routes}
    assert not any(
        action in path for path in paths for action in ("apply", "plan", "destroy")
    )


def test_api_proposal_retry_keeps_created_status_and_truthful_state() -> None:
    service = PlatformService()
    client = TestClient(create_app(service))
    assert (
        client.post("/v1/platform/installations", json={"provider": "aws"}).status_code
        == 201
    )
    request = client.post(
        "/v1/environment-requests",
        json=make_request().model_dump(mode="json"),
        headers={"Idempotency-Key": "proposal-state-request"},
    )
    request_id = request.json()["request"]["request_id"]
    body = {"request_id": request_id}
    first = client.post(
        "/v1/deployment-proposals",
        json=body,
        headers={"Idempotency-Key": "proposal-state"},
    )
    retry = client.post(
        "/v1/deployment-proposals",
        json=body,
        headers={"Idempotency-Key": "proposal-state"},
    )
    assert first.status_code == 201
    assert retry.status_code == 201
    assert first.json() == retry.json()
    assert first.json()["state"] == "ready_for_review"


@pytest.mark.parametrize("mode", ["sandbox", "enterprise"])
def test_api_accepts_proposal_only_modes(mode: str) -> None:
    service = PlatformService()
    client = TestClient(create_app(service))
    setup = client.post(
        "/v1/platform/installations",
        json={"provider": "aws", "mode": mode},
    )
    assert setup.status_code == 201
    descriptors = client.get("/v1/platform/modes").json()["modes"]
    descriptor = next(item for item in descriptors if item["mode"] == mode)
    assert descriptor["execution"] == "proposal-only"

    request = client.post(
        "/v1/environment-requests",
        json=make_request().model_dump(mode="json"),
        headers={"Idempotency-Key": f"{mode}-request"},
    )
    assert request.status_code == 200
    assert request.json()["state"] == "accepted"
    request_id = request.json()["request"]["request_id"]
    proposal = client.post(
        "/v1/deployment-proposals",
        json={"request_id": request_id},
        headers={"Idempotency-Key": f"{mode}-proposal"},
    )
    assert proposal.status_code == 201
    assert proposal.json()["mode"] == mode
    tfvars = next(
        artifact["content"]
        for artifact in proposal.json()["artifacts"]
        if artifact["relative_path"].endswith(".auto.tfvars.json")
    )
    assert json.loads(tfvars)["mode"] == mode
