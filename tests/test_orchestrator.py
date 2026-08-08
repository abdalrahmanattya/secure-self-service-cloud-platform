from datetime import date

import pytest

from conftest import request_with
from secure_cloud_platform import (
    AdapterProviderMismatchError,
    CloudProvider,
    MissingProviderAdapterError,
    PolicyViolation,
    ProviderAdapter,
    ProviderValidation,
    SimulationModeRequiredError,
    SimulationOrchestrator,
    SimulationResource,
)


class FakeAdapter:
    def __init__(
        self,
        provider: CloudProvider,
        *,
        installation_allowed: bool = True,
        request_allowed: bool = True,
    ) -> None:
        self.provider = provider
        self.installation_allowed = installation_allowed
        self.request_allowed = request_allowed
        self.installation_validation_calls = 0
        self.request_validation_calls = 0
        self.simulate_calls = 0

    def _validation(self, allowed: bool, code: str) -> ProviderValidation:
        violations = (
            ()
            if allowed
            else (
                PolicyViolation(
                    code=code,
                    message=f"The adapter rejected the request at {code}.",
                    field="provider",
                ),
            )
        )
        return ProviderValidation(allowed=allowed, violations=violations)

    def validate_installation(self, profile) -> ProviderValidation:
        self.installation_validation_calls += 1
        return self._validation(
            self.installation_allowed, "provider-installation-rejected"
        )

    def validate_request(self, request) -> ProviderValidation:
        self.request_validation_calls += 1
        return self._validation(self.request_allowed, "provider-request-rejected")

    def simulate(self, request) -> tuple[SimulationResource, ...]:
        self.simulate_calls += 1
        return (
            SimulationResource(
                kind="network",
                name=f"{request.application}-network",
                attributes=(("region", request.region),),
            ),
        )


@pytest.mark.parametrize(
    ("provider", "region"),
    [(CloudProvider.AWS, "eu-west-1"), (CloudProvider.AZURE, "northeurope")],
)
def test_both_provider_routes_simulate(
    profile_factory, request_model, provider, region
) -> None:
    profile = profile_factory(provider)
    request = request_with(request_model, region=region)
    adapter = FakeAdapter(provider)
    outcome = SimulationOrchestrator({provider: adapter}).simulate(
        profile, request, today=date(2026, 8, 8)
    )
    assert outcome.decision.allowed
    assert outcome.result is not None
    assert outcome.result.provider is provider
    assert adapter.installation_validation_calls == 1
    assert adapter.request_validation_calls == 1
    assert adapter.simulate_calls == 1


def test_common_denial_calls_neither_adapter_validation_nor_simulation(
    active_profile, request_model
) -> None:
    adapter = FakeAdapter(CloudProvider.AWS)
    denied_request = request_with(request_model, network_cidr="2001:db8::/64")
    outcome = SimulationOrchestrator({CloudProvider.AWS: adapter}).simulate(
        active_profile, denied_request, today=date(2026, 8, 8)
    )
    assert not outcome.decision.allowed
    assert outcome.result is None
    assert adapter.installation_validation_calls == 0
    assert adapter.request_validation_calls == 0
    assert adapter.simulate_calls == 0


def test_installation_provider_denial_stops_request_validation_and_simulation(
    active_profile, request_model
) -> None:
    adapter = FakeAdapter(CloudProvider.AWS, installation_allowed=False)
    outcome = SimulationOrchestrator({CloudProvider.AWS: adapter}).simulate(
        active_profile, request_model, today=date(2026, 8, 8)
    )
    assert not outcome.decision.allowed
    assert outcome.result is None
    assert adapter.installation_validation_calls == 1
    assert adapter.request_validation_calls == 0
    assert adapter.simulate_calls == 0


def test_request_provider_denial_stops_simulation(
    active_profile, request_model
) -> None:
    adapter = FakeAdapter(CloudProvider.AWS, request_allowed=False)
    outcome = SimulationOrchestrator({CloudProvider.AWS: adapter}).simulate(
        active_profile, request_model, today=date(2026, 8, 8)
    )
    assert not outcome.decision.allowed
    assert outcome.result is None
    assert adapter.installation_validation_calls == 1
    assert adapter.request_validation_calls == 1
    assert adapter.simulate_calls == 0


def test_unselected_adapter_is_never_called(active_profile, request_model) -> None:
    aws = FakeAdapter(CloudProvider.AWS)
    azure = FakeAdapter(CloudProvider.AZURE)
    outcome = SimulationOrchestrator(
        {CloudProvider.AWS: aws, CloudProvider.AZURE: azure}
    ).simulate(active_profile, request_model, today=date(2026, 8, 8))
    assert outcome.decision.allowed
    assert azure.installation_validation_calls == 0
    assert azure.request_validation_calls == 0
    assert azure.simulate_calls == 0


def test_provider_denial_never_simulates(active_profile, request_model) -> None:
    adapter = FakeAdapter(CloudProvider.AWS, request_allowed=False)
    outcome = SimulationOrchestrator({CloudProvider.AWS: adapter}).simulate(
        active_profile, request_model, today=date(2026, 8, 8)
    )
    assert not outcome.decision.allowed
    assert adapter.simulate_calls == 0


def test_missing_adapter_is_rejected(active_profile, request_model) -> None:
    with pytest.raises(MissingProviderAdapterError, match="no adapter"):
        SimulationOrchestrator(
            {CloudProvider.AZURE: FakeAdapter(CloudProvider.AZURE)}
        ).simulate(active_profile, request_model, today=date(2026, 8, 8))


def test_registry_mismatch_is_rejected(active_profile) -> None:
    with pytest.raises(AdapterProviderMismatchError):
        SimulationOrchestrator({CloudProvider.AWS: FakeAdapter(CloudProvider.AZURE)})


def test_non_cloud_provider_registry_key_is_typed_error() -> None:
    with pytest.raises(AdapterProviderMismatchError, match="CloudProvider"):
        SimulationOrchestrator({"aws": FakeAdapter(CloudProvider.AWS)})


def test_inconsistent_adapter_denial_is_rejected() -> None:
    with pytest.raises(ValueError, match="denied validation"):
        ProviderValidation(allowed=False)


def test_non_simulation_modes_require_explicit_simulation_mode(
    profile_factory, request_model
) -> None:
    profile = profile_factory(mode="sandbox")
    with pytest.raises(
        SimulationModeRequiredError, match="simulation installation mode"
    ):
        SimulationOrchestrator(
            {CloudProvider.AWS: FakeAdapter(CloudProvider.AWS)}
        ).simulate(profile, request_model, today=date(2026, 8, 8))


def test_only_base_adapter_port_is_runtime_checkable() -> None:
    adapter = FakeAdapter(CloudProvider.AZURE)
    assert isinstance(adapter, ProviderAdapter)
