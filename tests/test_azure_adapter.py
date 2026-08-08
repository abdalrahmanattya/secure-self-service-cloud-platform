import re
from decimal import Decimal

from conftest import request_with
from secure_cloud_platform import (
    CloudProvider,
    InstallationGuardrails,
    ProviderAdapter,
    ProviderValidation,
    ResolvedEnvironmentRequest,
)
from secure_cloud_platform.adapters import AzureProviderAdapter
from secure_cloud_platform.providers.azure import (
    SUPPORTED_AZURE_REGIONS,
    AzureSimulationAdapter,
)


def test_azure_adapter_protocol_and_provider_identity() -> None:
    adapter = AzureSimulationAdapter()

    assert isinstance(adapter, AzureProviderAdapter)
    assert isinstance(adapter, ProviderAdapter)
    assert adapter.provider is CloudProvider.AZURE
    assert (
        frozenset({"northeurope", "westeurope", "eastus", "westus2"})
        == SUPPORTED_AZURE_REGIONS
    )


def test_azure_installation_accepts_only_sanitized_supported_regions(
    profile_factory,
) -> None:
    adapter = AzureSimulationAdapter()
    profile = profile_factory(
        CloudProvider.AZURE,
        guardrails=InstallationGuardrails(
            allowed_regions=(" WestEurope ", "northeurope"),
            budget_maximum=Decimal("500"),
        ),
    )

    assert adapter.validate_installation(profile) == ProviderValidation(allowed=True)


def test_azure_installation_rejects_mixed_and_unsupported_regions(
    profile_factory,
) -> None:
    adapter = AzureSimulationAdapter()
    profile = profile_factory(
        CloudProvider.AZURE,
        guardrails=InstallationGuardrails(
            allowed_regions=("northeurope", "centralus", "WestEurope"),
            budget_maximum=Decimal("500"),
        ),
    )

    validation = adapter.validate_installation(profile)

    assert not validation.allowed
    assert [item.code for item in validation.violations] == ["azure-region-unsupported"]
    assert validation.violations[0].field == "guardrails.allowed_regions"
    assert "centralus" in validation.violations[0].message


def test_azure_installation_fails_closed_for_non_azure_profile(profile_factory) -> None:
    adapter = AzureSimulationAdapter()
    profile = profile_factory(CloudProvider.AWS)

    validation = adapter.validate_installation(profile)

    assert not validation.allowed
    assert validation.violations[0].code == "azure-provider-mismatch"
    assert all(item.code.startswith("azure-") for item in validation.violations)


def test_azure_request_fails_closed_for_non_azure_resolved_request(
    request_model,
) -> None:
    adapter = AzureSimulationAdapter()
    aws_request = ResolvedEnvironmentRequest(
        **request_model.model_dump(),
        provider=CloudProvider.AWS,
        canonical_json="{}",
        fingerprint="a" * 64,
        request_id="env-" + "a" * 16,
    )

    validation = adapter.validate_request(aws_request)

    assert not validation.allowed
    assert validation.violations[0].code == "azure-provider-mismatch"
    assert all(item.code.startswith("azure-") for item in validation.violations)


def test_azure_request_rejects_unsupported_region(request_model) -> None:
    adapter = AzureSimulationAdapter()
    request = request_with(request_model, region="centralus")
    resolved = ResolvedEnvironmentRequest(
        **request.model_dump(),
        provider=CloudProvider.AZURE,
        canonical_json="{}",
        fingerprint="b" * 64,
        request_id="env-" + "b" * 16,
    )

    validation = adapter.validate_request(resolved)

    assert not validation.allowed
    assert [item.code for item in validation.violations] == ["azure-region-unsupported"]
    assert validation.violations[0].field == "region"


def test_azure_simulation_contains_exact_security_resource_set(
    request_model,
) -> None:
    adapter = AzureSimulationAdapter()
    request = request_with(request_model, region="northeurope")
    resolved = ResolvedEnvironmentRequest(
        **request.model_dump(),
        provider=CloudProvider.AZURE,
        canonical_json="{}",
        fingerprint="c" * 64,
        request_id="env-" + "c" * 16,
    )

    resources = adapter.simulate(resolved)

    assert {resource.kind for resource in resources} == {
        "azure-vnet",
        "azure-aks",
        "azure-entra",
        "azure-key-vault",
        "azure-monitor",
        "azure-policy",
        "azure-private-endpoints",
        "azure-budget",
    }
    controls = {resource.kind: dict(resource.attributes) for resource in resources}
    assert controls["azure-vnet"]["private_subnets"] == "enabled"
    assert controls["azure-vnet"]["controlled_egress"] == "enabled"
    assert controls["azure-aks"]["api_server"] == "private"
    assert controls["azure-aks"]["kubernetes_version"] == "1.36"
    assert controls["azure-aks"]["network_plugin"] == "azure"
    assert controls["azure-entra"]["azure_rbac"] == "enabled"
    assert controls["azure-entra"]["workload_identity"] == "enabled"
    assert controls["azure-key-vault"]["encryption_at_rest"] == "enabled"
    assert controls["azure-monitor"]["activity_log"] == "enabled"
    assert controls["azure-monitor"]["log_analytics"] == "enabled"
    assert controls["azure-policy"]["defender_for_cloud"] == "enabled"
    assert controls["azure-private-endpoints"]["network_path"] == "vnet"
    assert controls["azure-budget"]["monthly_limit"] == "250.00"


def test_azure_simulation_is_deterministic_and_names_are_sanitized(
    request_model,
) -> None:
    adapter = AzureSimulationAdapter()
    request = request_with(
        request_model,
        application="Payments API / Production!",
        region="northeurope",
    )
    values = {
        **request.model_dump(),
        "provider": CloudProvider.AZURE,
        "canonical_json": "{}",
        "fingerprint": "d" * 64,
        "request_id": "env-" + "d" * 16,
    }
    first = adapter.simulate(ResolvedEnvironmentRequest(**values))
    second = adapter.simulate(ResolvedEnvironmentRequest(**values))

    assert first == second
    assert all(re.fullmatch(r"[a-z0-9-]+", item.name) for item in first)
    assert all("payments-api-production"[:20] in item.name for item in first)
    assert all("env-" + "d" * 16 in item.name for item in first)
    for item in first:
        values = " ".join(
            (item.name, *(value for pair in item.attributes for value in pair))
        ).lower()
        assert all(
            forbidden not in values
            for forbidden in ("tenant", "subscription", "credential", "https://")
        )


def test_azure_adapter_has_no_external_call_surface(request_model) -> None:
    adapter = AzureSimulationAdapter()
    resolved = ResolvedEnvironmentRequest(
        **request_model.model_dump(),
        provider=CloudProvider.AZURE,
        canonical_json="{}",
        fingerprint="e" * 64,
        request_id="env-" + "e" * 16,
    )

    assert vars(adapter) == {}
    assert all(
        not hasattr(adapter, attribute)
        for attribute in ("client", "session", "credentials", "subscription_id")
    )
    assert adapter.validate_request(resolved).allowed is False
    assert len(adapter.simulate(resolved)) == 8
