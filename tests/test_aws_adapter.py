import re
from decimal import Decimal

import pytest

from conftest import request_with
from secure_cloud_platform import (
    AWSProviderAdapter,
    CloudProvider,
    EnvironmentType,
    InstallationGuardrails,
    InstallationMode,
    ProviderAdapter,
    ProviderValidation,
    SimulationResource,
    SimulationResult,
    normalize_request,
)
from secure_cloud_platform.providers.aws import (
    SUPPORTED_AWS_REGIONS,
    AWSSimulationAdapter,
)


def _attributes(resource: SimulationResource) -> dict[str, str]:
    return dict(resource.attributes)


@pytest.fixture
def adapter() -> AWSSimulationAdapter:
    return AWSSimulationAdapter()


@pytest.fixture
def resolved_request(active_profile, request_model):
    return normalize_request(active_profile, request_model)


def test_adapter_has_aws_identity_and_implements_aws_protocol(adapter) -> None:
    assert adapter.provider is CloudProvider.AWS
    assert isinstance(adapter, ProviderAdapter)
    assert AWSProviderAdapter in AWSSimulationAdapter.__mro__


@pytest.mark.parametrize(
    "mode",
    [
        InstallationMode.SIMULATION,
        InstallationMode.SANDBOX,
        InstallationMode.ENTERPRISE,
    ],
)
def test_aws_installation_accepts_all_profile_modes_at_adapter_boundary(
    adapter, profile_factory, mode
) -> None:
    profile = profile_factory(
        CloudProvider.AWS,
        mode=mode,
        guardrails=InstallationGuardrails(
            allowed_regions=("EU-WEST-1", "us-east-1"),
            budget_maximum=Decimal("500.00"),
        ),
    )

    validation = adapter.validate_installation(profile)

    assert validation == ProviderValidation(allowed=True)


def test_installation_provider_mismatch_fails_closed(adapter, profile_factory) -> None:
    profile = profile_factory(CloudProvider.AZURE)

    validation = adapter.validate_installation(profile)

    assert not validation.allowed
    assert any(
        violation.code == "aws-provider-mismatch" and violation.field == "provider"
        for violation in validation.violations
    )


def test_installation_region_allowlist_must_be_fully_supported(
    adapter, profile_factory
) -> None:
    profile = profile_factory(
        CloudProvider.AWS,
        guardrails=InstallationGuardrails(
            allowed_regions=("eu-west-1", "example-region", "us-west-2")
        ),
    )

    validation = adapter.validate_installation(profile)

    assert not validation.allowed
    assert validation.violations[0].code == "aws-region-unsupported"
    assert validation.violations[0].field == "guardrails.allowed_regions"


def test_request_provider_mismatch_fails_closed(
    adapter, request_model, profile_factory
) -> None:
    azure_request = normalize_request(
        profile_factory(CloudProvider.AZURE), request_model
    )

    validation = adapter.validate_request(azure_request)

    assert not validation.allowed
    assert validation.violations[0].code == "aws-provider-mismatch"
    assert validation.violations[0].field == "provider"


def test_request_region_must_be_supported(
    adapter, request_model, active_profile
) -> None:
    request = request_with(request_model, region="ap-southeast-1")
    resolved = normalize_request(active_profile, request)

    validation = adapter.validate_request(resolved)

    assert not validation.allowed
    assert validation.violations[0].code == "aws-region-unsupported"
    assert validation.violations[0].field == "region"


def test_supported_region_set_is_sanitized_and_closed() -> None:
    assert {
        "eu-west-1",
        "eu-central-1",
        "us-east-1",
        "us-west-2",
    } == SUPPORTED_AWS_REGIONS
    assert all(region == region.lower() for region in SUPPORTED_AWS_REGIONS)


def test_simulation_contains_exact_aws_controls(adapter, resolved_request) -> None:
    resources = adapter.simulate(resolved_request)
    by_kind = {resource.kind: _attributes(resource) for resource in resources}

    assert set(by_kind) == {
        "aws-budget",
        "aws-cloudtrail",
        "aws-eks",
        "aws-guardduty",
        "aws-iam",
        "aws-kms",
        "aws-secrets-manager",
        "aws-vpc",
    }
    assert by_kind["aws-vpc"] == {
        "address_space": "10.42.0.0/16",
        "availability_zones": "2",
        "controlled_egress": "enabled",
        "nat_gateways": "1",
        "nat_strategy": "single",
        "private_subnets": "enabled",
        "vpc_endpoints": "enabled",
    }
    assert by_kind["aws-eks"] == {
        "api_endpoint": "private",
        "control_plane_logs": "all",
        "encryption": "kms",
        "nodes": "private",
        "version": "1.36",
    }
    assert by_kind["aws-iam"]["irsa"] == "enabled"
    assert by_kind["aws-iam"]["least_privilege"] == "enabled"
    assert by_kind["aws-kms"]["key_rotation"] == "enabled"
    assert by_kind["aws-secrets-manager"]["encryption"] == "kms"
    assert by_kind["aws-cloudtrail"]["cloudwatch"] == "enabled"
    assert by_kind["aws-guardduty"]["security_hub"] == "enabled"
    assert by_kind["aws-budget"] == {
        "alerts": "80,100",
        "monthly_limit": "250.00",
        "scope": "application",
    }


def test_simulation_uses_production_topology(
    adapter, active_profile, request_model
) -> None:
    request = request_with(
        request_model,
        environment=EnvironmentType.PRODUCTION,
        non_production_expiry=None,
    )
    resolved = normalize_request(active_profile, request)
    by_kind = {
        resource.kind: _attributes(resource) for resource in adapter.simulate(resolved)
    }

    assert by_kind["aws-vpc"]["availability_zones"] == "3"
    assert by_kind["aws-vpc"]["nat_gateways"] == "3"
    assert by_kind["aws-vpc"]["nat_strategy"] == "per-az"


def test_simulation_is_deterministic_and_model_sorting_is_stable(
    adapter, resolved_request
) -> None:
    first = adapter.simulate(resolved_request)
    second = adapter.simulate(resolved_request)

    assert first == second
    assert all(
        isinstance(value, str)
        for resource in first
        for attribute in resource.attributes
        for value in attribute
    )
    result = SimulationResult(
        provider=CloudProvider.AWS,
        request_id=resolved_request.request_id,
        fingerprint=resolved_request.fingerprint,
        resources=tuple(reversed(first)),
    )
    assert result.resources == tuple(
        sorted(first, key=lambda item: (item.kind, item.name, item.attributes))
    )


def test_simulation_names_are_sanitized_and_derive_from_request_identity(
    adapter, active_profile, request_model
) -> None:
    request = request_with(request_model, application="Payments/API _ Prod!!!")
    resolved = normalize_request(active_profile, request)
    resources = adapter.simulate(resolved)

    assert all(
        re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", resource.name)
        for resource in resources
    )
    assert all("scp-payments-api-prod" in resource.name for resource in resources)
    assert all(resolved.request_id in resource.name for resource in resources)
    assert not any(
        token in resource.name.lower()
        for resource in resources
        for token in ("arn:", "account", "credential")
    )


def test_adapter_has_no_external_call_surface(adapter, resolved_request) -> None:
    assert set(vars(adapter)) == set()
    assert all(
        not hasattr(adapter, attribute)
        for attribute in (
            "client",
            "session",
            "credentials",
            "account_id",
            "region_client",
        )
    )
    assert len(adapter.simulate(resolved_request)) == 8
