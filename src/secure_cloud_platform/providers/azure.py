"""Credential-free Azure simulation adapter.

This module describes the Azure design without importing Azure SDKs or making
network calls.  It is deliberately a leaf implementation behind the neutral
adapter protocol.
"""

from __future__ import annotations

import re
from typing import Final, Literal

from ..adapters import AzureProviderAdapter
from ..models import (
    CloudProvider,
    InstallationProfile,
    PolicyViolation,
    ProviderValidation,
    ResolvedEnvironmentRequest,
    SimulationResource,
)

SUPPORTED_AZURE_REGIONS: Final[frozenset[str]] = frozenset(
    {"northeurope", "westeurope", "eastus", "westus2"}
)
"""Azure regions accepted by the credential-free simulation boundary."""
AZURE_KUBERNETES_VERSION: Final[str] = "1.36"

_SAFE_NAME = re.compile(r"[^a-z0-9-]+")


def _violation(code: str, message: str, field: str) -> PolicyViolation:
    """Create a provider-neutral, user-facing Azure policy violation."""

    return PolicyViolation(code=code, message=message, field=field)


def _safe_name(application: str, request_id: str, suffix: str) -> str:
    """Return a bounded, lowercase name containing only Azure-safe characters."""

    application_slug = _SAFE_NAME.sub("-", application.lower()).strip("-")
    application_slug = application_slug[:20].strip("-") or "application"
    # request_id is already an immutable normalized identity.  Keeping it in
    # every name makes the simulation easy to correlate without an external ID.
    return f"scp-{application_slug}-{request_id}-{suffix}"


def _resource(
    request: ResolvedEnvironmentRequest,
    *,
    kind: str,
    suffix: str,
    attributes: tuple[tuple[str, str], ...],
) -> SimulationResource:
    return SimulationResource(
        kind=kind,
        name=_safe_name(request.application, request.request_id, suffix),
        attributes=attributes,
    )


class AzureSimulationAdapter(AzureProviderAdapter):
    """Describe an Azure landing zone for one normalized environment request.

    The adapter only evaluates immutable domain values and constructs neutral
    simulation descriptions.  It has no Azure SDK, credential, environment
    variable, filesystem, or network access.
    """

    @property
    def provider(self) -> Literal[CloudProvider.AZURE]:
        return CloudProvider.AZURE

    def validate_installation(self, profile: InstallationProfile) -> ProviderValidation:
        """Reject non-Azure profiles and every region outside the safe allowlist."""

        violations: list[PolicyViolation] = []
        if profile.provider is not CloudProvider.AZURE:
            violations.append(
                _violation(
                    "azure-provider-mismatch",
                    "The Azure adapter requires an installation configured for Azure.",
                    "provider",
                )
            )

        unsupported = sorted(
            set(profile.guardrails.allowed_regions) - SUPPORTED_AZURE_REGIONS
        )
        if unsupported:
            regions = ", ".join(unsupported)
            violations.append(
                _violation(
                    "azure-region-unsupported",
                    "Azure simulation supports only northeurope, westeurope, "
                    "eastus, and westus2; unsupported installation regions: "
                    f"{regions}.",
                    "guardrails.allowed_regions",
                )
            )

        return ProviderValidation(allowed=not violations, violations=tuple(violations))

    def validate_request(
        self, request: ResolvedEnvironmentRequest
    ) -> ProviderValidation:
        """Reject non-Azure requests and regions outside the safe allowlist."""

        violations: list[PolicyViolation] = []
        if request.provider is not CloudProvider.AZURE:
            violations.append(
                _violation(
                    "azure-provider-mismatch",
                    "The Azure adapter requires a request resolved to Azure.",
                    "provider",
                )
            )
        if request.region not in SUPPORTED_AZURE_REGIONS:
            supported = ", ".join(sorted(SUPPORTED_AZURE_REGIONS))
            violations.append(
                _violation(
                    "azure-region-unsupported",
                    "The Azure request region is not supported; choose one of "
                    f"{supported}.",
                    "region",
                )
            )

        return ProviderValidation(allowed=not violations, violations=tuple(violations))

    def simulate(
        self, request: ResolvedEnvironmentRequest
    ) -> tuple[SimulationResource, ...]:
        """Return deterministic Azure resource descriptions for the request."""

        return (
            _resource(
                request,
                kind="azure-vnet",
                suffix="vnet",
                attributes=(
                    ("address_space", str(request.network_cidr)),
                    ("private_subnets", "enabled"),
                    ("controlled_egress", "enabled"),
                    ("network_security_groups", "enabled"),
                ),
            ),
            _resource(
                request,
                kind="azure-aks",
                suffix="aks",
                attributes=(
                    ("api_server", "private"),
                    ("kubernetes_version", AZURE_KUBERNETES_VERSION),
                    ("network_plugin", "azure"),
                    ("nodes", "private"),
                ),
            ),
            _resource(
                request,
                kind="azure-entra",
                suffix="entra",
                attributes=(
                    ("azure_rbac", "enabled"),
                    ("managed_identity", "enabled"),
                    ("workload_identity", "enabled"),
                ),
            ),
            _resource(
                request,
                kind="azure-key-vault",
                suffix="key-vault",
                attributes=(
                    ("encryption_at_rest", "enabled"),
                    ("private_access", "enabled"),
                    ("purge_protection", "enabled"),
                    ("soft_delete", "enabled"),
                ),
            ),
            _resource(
                request,
                kind="azure-monitor",
                suffix="monitor",
                attributes=(
                    ("activity_log", "enabled"),
                    ("diagnostic_settings", "enabled"),
                    ("log_analytics", "enabled"),
                ),
            ),
            _resource(
                request,
                kind="azure-policy",
                suffix="policy",
                attributes=(
                    ("azure_policy", "enabled"),
                    ("defender_for_cloud", "enabled"),
                    ("deny_public_access", "enabled"),
                ),
            ),
            _resource(
                request,
                kind="azure-private-endpoints",
                suffix="private-endpoints",
                attributes=(
                    ("aks", "private"),
                    ("key_vault", "private"),
                    ("monitoring", "private"),
                    ("network_path", "vnet"),
                ),
            ),
            _resource(
                request,
                kind="azure-budget",
                suffix="budget",
                attributes=(
                    ("alert_thresholds", "80,100"),
                    ("monthly_limit", str(request.monthly_budget)),
                    ("scope", "environment"),
                ),
            ),
        )
