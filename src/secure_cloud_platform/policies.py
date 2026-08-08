"""Deterministic common policy evaluation."""

from __future__ import annotations

from datetime import date, timedelta
from ipaddress import ip_network

from .models import (
    EnvironmentType,
    InstallationMode,
    InstallationProfile,
    InstallationStatus,
    PolicyDecision,
    PolicyViolation,
    ResolvedEnvironmentRequest,
)


def _violation(code: str, message: str, field: str) -> PolicyViolation:
    return PolicyViolation(code=code, message=message, field=field)


def evaluate_common_policies(
    profile: InstallationProfile,
    request: ResolvedEnvironmentRequest,
    *,
    today: date,
) -> PolicyDecision:
    """Evaluate shared governance rules in stable order."""

    violations: list[PolicyViolation] = []
    if profile.status is not InstallationStatus.ACTIVE:
        violations.append(
            _violation(
                "installation-not-active",
                "The installation must be active before environments can be requested.",
                "installation.status",
            )
        )

    if profile.provider is None or profile.provider is not request.provider:
        violations.append(
            _violation(
                "provider-mismatch",
                "The request provider must match the installation provider.",
                "provider",
            )
        )

    try:
        network = ip_network(str(request.network_cidr), strict=False)
    except ValueError:
        network = None
    if network is None or network.version != 4 or not network.is_private:
        violations.append(
            _violation(
                "network-must-be-private-ipv4",
                "The network must use a private IPv4 CIDR.",
                "network_cidr",
            )
        )

    if request.region not in profile.guardrails.allowed_regions:
        violations.append(
            _violation(
                "region-not-allowed",
                "The requested region is not enabled for this installation.",
                "region",
            )
        )

    if request.monthly_budget > profile.guardrails.budget_maximum:
        violations.append(
            _violation(
                "budget-exceeds-maximum",
                "The monthly budget exceeds the installation maximum.",
                "monthly_budget",
            )
        )

    if request.cluster_size not in profile.guardrails.allowed_cluster_sizes:
        violations.append(
            _violation(
                "cluster-size-not-allowed",
                "The requested cluster size is not enabled for this installation.",
                "cluster_size",
            )
        )

    if (
        profile.mode is InstallationMode.SANDBOX
        and request.environment is EnvironmentType.PRODUCTION
    ):
        violations.append(
            _violation(
                "sandbox-production-forbidden",
                "Sandbox installations cannot create production environments.",
                "environment",
            )
        )

    if request.environment is not EnvironmentType.PRODUCTION:
        expiry = request.non_production_expiry
        if expiry is None:
            violations.append(
                _violation(
                    "nonproduction-expiry-required",
                    "Non-production environments must have an expiry date.",
                    "non_production_expiry",
                )
            )
        else:
            if expiry <= today:
                violations.append(
                    _violation(
                        "nonproduction-expiry-not-future",
                        "The non-production expiry date must be in the future.",
                        "non_production_expiry",
                    )
                )
            latest = today + timedelta(
                days=profile.guardrails.max_nonproduction_lifetime_days
            )
            if expiry > latest:
                violations.append(
                    _violation(
                        "nonproduction-expiry-too-long",
                        "The non-production expiry exceeds the installation "
                        "lifetime limit.",
                        "non_production_expiry",
                    )
                )

    return PolicyDecision(allowed=not violations, violations=tuple(violations))


def merge_decisions(*decisions: PolicyDecision) -> PolicyDecision:
    """Merge decisions with stable sorting and exact duplicate removal."""

    unique = {
        (violation.code, violation.field, violation.message): violation
        for decision in decisions
        for violation in decision.violations
    }
    violations = tuple(
        unique[key]
        for key in sorted(unique, key=lambda item: (item[0], item[1], item[2]))
    )
    return PolicyDecision(allowed=not violations, violations=violations)
