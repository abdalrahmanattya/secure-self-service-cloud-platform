from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal

import pytest

from secure_cloud_platform import (
    CloudProvider,
    EnvironmentRequest,
    ProviderValidation,
    SimulationResource,
)
from secure_cloud_platform.providers.aws import AWSSimulationAdapter
from secure_cloud_platform.providers.azure import AzureSimulationAdapter
from secure_cloud_platform.service import (
    IdempotencyConflictError,
    IdempotencyKeyRequiredError,
    InstallationNotFoundError,
    InstallationRejectedError,
    PlatformService,
)


class SimulationAdapter:
    def __init__(self, provider: CloudProvider) -> None:
        self.provider = provider

    def validate_installation(self, profile) -> ProviderValidation:
        return ProviderValidation(allowed=True)

    def validate_request(self, request) -> ProviderValidation:
        return ProviderValidation(allowed=True)

    def simulate(self, request) -> tuple[SimulationResource, ...]:
        return (
            SimulationResource(
                kind="network",
                name=f"{request.application}-network",
                attributes=(("provider", request.provider.value),),
            ),
        )


def make_request(**updates: object) -> EnvironmentRequest:
    values: dict[str, object] = {
        "application": "payments-api",
        "environment": "development",
        "owner": "Platform Team",
        "cost_centre": "FIN-042",
        "data_classification": "internal",
        "region": "eu-west-1",
        "network_cidr": "10.42.0.0/16",
        "cluster_size": "small",
        "monthly_budget": Decimal("250.00"),
        "business_justification": "development environment",
        "non_production_expiry": date(2026, 8, 20),
    }
    values.update(updates)
    return EnvironmentRequest(**values)


def make_service() -> PlatformService:
    return PlatformService(
        {
            CloudProvider.AWS: SimulationAdapter(CloudProvider.AWS),
            CloudProvider.AZURE: SimulationAdapter(CloudProvider.AZURE),
        },
        today=date(2026, 8, 8),
    )


@pytest.mark.parametrize(
    ("provider", "region"),
    [(CloudProvider.AWS, "eu-west-1"), (CloudProvider.AZURE, "northeurope")],
)
def test_service_simulates_both_provider_routes(provider, region) -> None:
    service = make_service()
    service.create_installation(
        provider=provider,
        guardrails={
            "allowed_regions": (region,),
            "budget_maximum": "500.00",
        },
    )
    record = service.create_environment_request(
        make_request(region=region), idempotency_key=f"key-{provider.value}"
    )
    assert record.state == "accepted"
    assert record.request.provider is provider
    assert record.outcome.result is not None
    assert record.outcome.result.request_id == record.request.request_id


def test_service_idempotency_is_normalized_and_conflicts() -> None:
    service = make_service()
    service.create_installation(
        provider="aws",
        guardrails={"allowed_regions": ("eu-west-1",)},
    )
    first = service.create_environment_request(
        make_request(application=" payments-api "), idempotency_key="same-key"
    )
    second = service.create_environment_request(
        make_request(application="payments-api"), idempotency_key="same-key"
    )
    assert first == second
    aliased = service.create_environment_request(
        make_request(), idempotency_key="another-key"
    )
    assert aliased == first
    assert aliased.idempotency_key == "same-key"
    with pytest.raises(IdempotencyConflictError):
        service.create_environment_request(
            make_request(application="different-api"), idempotency_key="same-key"
        )


def test_service_requires_key_and_keeps_denied_results() -> None:
    service = make_service()
    service.create_installation(
        provider="aws",
        guardrails={"allowed_regions": ("eu-west-1",)},
    )
    for key in (None, " "):
        with pytest.raises(IdempotencyKeyRequiredError):
            service.create_environment_request(make_request(), idempotency_key=key)
    denied = service.create_environment_request(
        make_request(network_cidr="8.8.8.0/24"), idempotency_key="denied"
    )
    assert denied.state == "denied"
    assert denied.outcome.result is None
    assert denied.outcome.decision.violations[0].field == "network_cidr"


@pytest.mark.parametrize("mode", ["simulation", "sandbox", "enterprise"])
def test_all_installation_modes_evaluate_requests_without_cloud_access(mode) -> None:
    service = make_service()
    service.create_installation(provider="aws", mode=mode)
    record = service.create_environment_request(
        make_request(), idempotency_key=f"mode-{mode}"
    )
    assert record.state == "accepted"
    assert record.request.provider is CloudProvider.AWS
    assert record.outcome.result is not None


@pytest.mark.parametrize(
    ("provider", "region"),
    [(CloudProvider.AWS, "eu-west-1"), (CloudProvider.AZURE, "northeurope")],
)
def test_provider_defaults_and_real_adapters_validate(provider, region) -> None:
    adapters = {
        CloudProvider.AWS: AWSSimulationAdapter(),
        CloudProvider.AZURE: AzureSimulationAdapter(),
    }
    service = PlatformService(adapters, today=date(2026, 8, 8))
    profile = service.create_installation(provider=provider)
    assert profile.guardrails.allowed_regions == (region,)
    assert service.validate_installation().allowed


def test_rejected_setup_leaves_service_unset_and_can_retry() -> None:
    service = PlatformService(
        {
            CloudProvider.AWS: AWSSimulationAdapter(),
            CloudProvider.AZURE: AzureSimulationAdapter(),
        }
    )
    with pytest.raises(InstallationRejectedError) as error:
        service.create_installation(
            provider=CloudProvider.AWS,
            guardrails={"allowed_regions": ("northeurope",)},
        )
    assert error.value.validation.violations[0].field == "guardrails.allowed_regions"
    with pytest.raises(InstallationNotFoundError):
        service.get_installation()
    profile = service.create_installation(provider=CloudProvider.AZURE)
    assert profile.provider is CloudProvider.AZURE


def test_concurrent_identical_submissions_share_one_record() -> None:
    service = make_service()
    service.create_installation(
        provider="aws",
        guardrails={"allowed_regions": ("eu-west-1",)},
    )
    request = make_request()

    def submit(index: int):
        return service.create_environment_request(
            request, idempotency_key=f"concurrent-{index}"
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        records = list(executor.map(submit, range(8)))
    assert all(record == records[0] for record in records)
    assert records[0].idempotency_key.startswith("concurrent-")
    assert len(service.list_environment_requests()) == 1
