from datetime import date

import pytest
from pydantic import ValidationError

from secure_cloud_platform import (
    CloudProvider,
    EnvironmentRequest,
    InstallationConfigurationError,
    InstallationGuardrails,
    InstallationProfile,
    InstallationStatus,
    InvalidLifecycleTransitionError,
    PolicyDecision,
    PolicyViolation,
    ProviderLockedError,
    ProviderValidation,
    SimulationOutcome,
    SimulationResource,
    SimulationResult,
)


def test_raw_request_has_no_provider_field(request_model: EnvironmentRequest) -> None:
    assert "provider" not in EnvironmentRequest.model_fields
    assert "provider" not in request_model.model_dump()


def test_profile_lifecycle_locks_provider_after_activation() -> None:
    profile = InstallationProfile(installation_id="demo").with_provider(
        CloudProvider.AZURE
    )
    active = profile.activate()
    assert active.status is InstallationStatus.ACTIVE
    assert active.provider is CloudProvider.AZURE
    with pytest.raises(ProviderLockedError):
        active.with_provider(CloudProvider.AWS)
    retired = active.retire()
    with pytest.raises(ProviderLockedError):
        retired.with_provider(CloudProvider.AWS)


def test_lifecycle_reconstruction_validates_provider_input() -> None:
    draft = InstallationProfile(installation_id="demo")
    with pytest.raises(ValidationError):
        draft.with_provider("not-a-cloud-provider")
    active = draft.with_provider("azure").activate()
    assert active.provider is CloudProvider.AZURE
    assert active.status is InstallationStatus.ACTIVE


def test_guardrail_region_default_is_provider_neutral() -> None:
    guardrails = InstallationGuardrails()
    assert guardrails.allowed_regions == ("example-region",)
    assert all(
        region not in {"eu-west-1", "northeurope"}
        for region in guardrails.allowed_regions
    )


def test_lifecycle_rejects_missing_provider_and_invalid_transitions() -> None:
    profile = InstallationProfile(installation_id="demo")
    with pytest.raises(
        InstallationConfigurationError, match="provider must be selected"
    ):
        profile.activate()
    with pytest.raises(InvalidLifecycleTransitionError):
        profile.retire()
    active = profile.with_provider(CloudProvider.AWS).activate()
    with pytest.raises(InvalidLifecycleTransitionError):
        active.retire().retire()


def test_models_are_immutable(request_model: EnvironmentRequest) -> None:
    with pytest.raises(ValidationError):
        request_model.application = "changed"  # type: ignore[misc]


def test_profile_rejects_active_or_retired_without_provider() -> None:
    for status in (InstallationStatus.ACTIVE, InstallationStatus.RETIRED):
        with pytest.raises(ValidationError, match="require a provider"):
            InstallationProfile(installation_id="demo", status=status)


def test_request_accepts_networks_for_policy_evaluation() -> None:
    for network_cidr in ("8.8.8.0/24", "2001:db8::/64"):
        request = EnvironmentRequest(
            application="app",
            environment="test",
            owner="owner",
            cost_centre="cc",
            data_classification="internal",
            region="eu-west-1",
            network_cidr=network_cidr,
            cluster_size="small",
            monthly_budget="10",
            business_justification="reason",
            non_production_expiry=date(2026, 8, 20),
        )
        assert str(request.network_cidr) == network_cidr


def test_raw_request_rejects_injected_provider() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        EnvironmentRequest(
            application="app",
            environment="test",
            owner="owner",
            cost_centre="cc",
            data_classification="internal",
            region="eu-west-1",
            network_cidr="10.0.0.0/24",
            cluster_size="small",
            monthly_budget="10",
            business_justification="reason",
            non_production_expiry=date(2026, 8, 20),
            provider="aws",
        )


def test_inconsistent_decisions_and_validations_are_rejected() -> None:
    violation = PolicyViolation(code="denied", message="Denied", field="request")
    with pytest.raises(ValidationError):
        PolicyDecision(allowed=True, violations=(violation,))
    with pytest.raises(ValidationError):
        PolicyDecision(allowed=False)
    with pytest.raises(ValidationError):
        ProviderValidation(allowed=True, violations=(violation,))
    with pytest.raises(ValidationError):
        ProviderValidation(allowed=False)


def test_validation_violations_are_sorted_and_deduplicated() -> None:
    region = PolicyViolation(code="region", message="Region denied", field="region")
    budget = PolicyViolation(code="budget", message="Budget denied", field="budget")
    validation = ProviderValidation(allowed=False, violations=(region, budget, region))
    assert validation.violations == (budget, region)


def test_outcome_requires_result_exactly_when_allowed() -> None:
    violation = PolicyViolation(code="denied", message="Denied", field="request")
    denied = PolicyDecision(allowed=False, violations=(violation,))
    allowed = PolicyDecision(allowed=True)
    result = SimulationResult(
        provider="aws",
        request_id="env-0123456789abcdef",
        fingerprint="0" * 64,
        resources=(),
    )
    with pytest.raises(ValidationError):
        SimulationOutcome(decision=allowed)
    with pytest.raises(ValidationError):
        SimulationOutcome(decision=denied, result=result)
    assert SimulationOutcome(decision=allowed, result=result).result == result


def test_guardrails_normalize_and_validate_cluster_sizes() -> None:
    guardrails = InstallationGuardrails(
        allowed_cluster_sizes=("large", "small", "large")
    )
    assert guardrails.allowed_cluster_sizes == ("large", "small")
    with pytest.raises(ValidationError, match="must not be empty"):
        InstallationGuardrails(allowed_cluster_sizes=())


def test_simulation_resources_and_results_are_deterministic() -> None:
    with pytest.raises(ValidationError, match="keys must be unique"):
        SimulationResource(
            kind="network", name="n", attributes=(("z", "1"), ("z", "2"))
        )
    second = SimulationResource(kind="z", name="b", attributes=(("z", "1"),))
    first = SimulationResource(kind="a", name="c", attributes=(("a", "1"),))
    attributes = SimulationResource(
        kind="attributes", name="sorted", attributes=(("z", "1"), ("a", "2"))
    )
    assert attributes.attributes == (("a", "2"), ("z", "1"))
    result = SimulationResult(
        provider="aws",
        request_id="env-0123456789abcdef",
        fingerprint="0" * 64,
        resources=(second, first),
    )
    assert result.resources == (first, second)


def test_simulation_result_rejects_invalid_identity_formats() -> None:
    with pytest.raises(ValidationError):
        SimulationResult(
            provider="aws",
            request_id="request-1",
            fingerprint="0" * 64,
            resources=(),
        )
    with pytest.raises(ValidationError):
        SimulationResult(
            provider="aws",
            request_id="env-0123456789abcdef",
            fingerprint="not-a-fingerprint",
            resources=(),
        )
    with pytest.raises(ValidationError):
        SimulationResult(
            provider="aws",
            request_id="env-0123456789ABCDEF",
            fingerprint="0" * 64,
            resources=(),
        )
    with pytest.raises(ValidationError):
        SimulationResult(
            provider="aws",
            request_id="env-0123456789abcdef",
            fingerprint="A" * 64,
            resources=(),
        )
