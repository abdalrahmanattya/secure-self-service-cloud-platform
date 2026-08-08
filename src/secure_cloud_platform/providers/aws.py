"""Credential-free, deterministic AWS simulation adapter."""

from __future__ import annotations

import re
from typing import Final, Literal

from ..adapters import AWSProviderAdapter
from ..models import (
    CloudProvider,
    EnvironmentType,
    InstallationProfile,
    PolicyViolation,
    ProviderValidation,
    ResolvedEnvironmentRequest,
    SimulationResource,
)

SUPPORTED_AWS_REGIONS: Final[frozenset[str]] = frozenset(
    {"eu-west-1", "eu-central-1", "us-east-1", "us-west-2"}
)
"""AWS regions accepted by the credential-free simulation boundary."""

AWS_KUBERNETES_VERSION: Final[str] = "1.36"
_SAFE_NAME = re.compile(r"[^a-z0-9-]+")
_MAX_APPLICATION_SLUG_LENGTH = 20


def _violation(code: str, message: str, field: str) -> PolicyViolation:
    return PolicyViolation(code=code, message=message, field=field)


def _safe_name(application: str, request_id: str, suffix: str) -> str:
    """Return a bounded, lower-case name containing safe characters."""

    slug = _SAFE_NAME.sub("-", application.lower()).strip("-")
    slug = slug[:_MAX_APPLICATION_SLUG_LENGTH].strip("-") or "application"
    return f"scp-{slug}-{request_id}-{suffix}"


def _resource(
    request: ResolvedEnvironmentRequest,
    kind: str,
    component: str,
    attributes: tuple[tuple[str, str], ...],
) -> SimulationResource:
    """Construct a resource while keeping every simulated attribute textual."""

    return SimulationResource(
        kind=kind,
        name=_safe_name(request.application, request.request_id, component),
        attributes=tuple((str(key), str(value)) for key, value in attributes),
    )


class AWSSimulationAdapter(AWSProviderAdapter):
    """Describe a secure AWS environment without SDKs, credentials, or calls."""

    @property
    def provider(self) -> Literal[CloudProvider.AWS]:
        return CloudProvider.AWS

    def validate_installation(self, profile: InstallationProfile) -> ProviderValidation:
        """Fail closed unless the profile is AWS and all regions are supported."""

        violations: list[PolicyViolation] = []
        if profile.provider is not CloudProvider.AWS:
            violations.append(
                _violation(
                    "aws-provider-mismatch",
                    "The installation provider must be AWS for AWS-specific "
                    "validation.",
                    "provider",
                )
            )

        unsupported_regions = sorted(
            set(profile.guardrails.allowed_regions) - SUPPORTED_AWS_REGIONS
        )
        if unsupported_regions:
            regions = ", ".join(unsupported_regions)
            violations.append(
                _violation(
                    "aws-region-unsupported",
                    "AWS simulation supports only eu-west-1, eu-central-1, us-east-1, "
                    "and us-west-2; unsupported installation regions: "
                    f"{regions}.",
                    "guardrails.allowed_regions",
                )
            )

        return ProviderValidation(allowed=not violations, violations=tuple(violations))

    def validate_request(
        self, request: ResolvedEnvironmentRequest
    ) -> ProviderValidation:
        """Fail closed unless the resolved request is AWS and region-supported."""

        violations: list[PolicyViolation] = []
        if request.provider is not CloudProvider.AWS:
            violations.append(
                _violation(
                    "aws-provider-mismatch",
                    "The request provider must be AWS for AWS-specific validation.",
                    "provider",
                )
            )
        if request.region not in SUPPORTED_AWS_REGIONS:
            supported = ", ".join(sorted(SUPPORTED_AWS_REGIONS))
            violations.append(
                _violation(
                    "aws-region-unsupported",
                    "The AWS request region is not supported; choose one of "
                    f"{supported}.",
                    "region",
                )
            )

        return ProviderValidation(allowed=not violations, violations=tuple(violations))

    def simulate(
        self, request: ResolvedEnvironmentRequest
    ) -> tuple[SimulationResource, ...]:
        """Return the fixed secure AWS topology for the requested environment."""

        production = request.environment is EnvironmentType.PRODUCTION
        availability_zones = "3" if production else "2"
        nat_gateways = availability_zones if production else "1"
        nat_strategy = "per-az" if production else "single"
        budget = str(request.monthly_budget)

        return (
            _resource(
                request,
                "aws-vpc",
                "network",
                (
                    ("address_space", str(request.network_cidr)),
                    ("availability_zones", availability_zones),
                    ("controlled_egress", "enabled"),
                    ("nat_gateways", nat_gateways),
                    ("nat_strategy", nat_strategy),
                    ("private_subnets", "enabled"),
                    ("vpc_endpoints", "enabled"),
                ),
            ),
            _resource(
                request,
                "aws-eks",
                "eks",
                (
                    ("api_endpoint", "private"),
                    ("control_plane_logs", "all"),
                    ("encryption", "kms"),
                    ("nodes", "private"),
                    ("version", AWS_KUBERNETES_VERSION),
                ),
            ),
            _resource(
                request,
                "aws-iam",
                "identity",
                (
                    ("irsa", "enabled"),
                    ("least_privilege", "enabled"),
                    ("static_credentials", "forbidden"),
                ),
            ),
            _resource(
                request,
                "aws-kms",
                "encryption",
                (
                    ("key_rotation", "enabled"),
                    ("scope", "eks-and-secrets"),
                    ("storage_encryption", "enabled"),
                ),
            ),
            _resource(
                request,
                "aws-secrets-manager",
                "secrets",
                (
                    ("encryption", "kms"),
                    ("provider", "secrets-manager"),
                    ("secret_values", "not-materialized"),
                ),
            ),
            _resource(
                request,
                "aws-cloudtrail",
                "audit-logging",
                (
                    ("cloudtrail", "enabled"),
                    ("cloudwatch", "enabled"),
                    ("log_validation", "enabled"),
                    ("management_events", "all"),
                ),
            ),
            _resource(
                request,
                "aws-guardduty",
                "security-detection",
                (
                    ("finding_aggregation", "enabled"),
                    ("guardduty", "enabled"),
                    ("security_hub", "enabled"),
                ),
            ),
            _resource(
                request,
                "aws-budget",
                "budget",
                (
                    ("alerts", "80,100"),
                    ("monthly_limit", budget),
                    ("scope", "application"),
                ),
            ),
        )
