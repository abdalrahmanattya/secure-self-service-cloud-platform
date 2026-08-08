from datetime import date
from decimal import Decimal

import pytest

from conftest import request_with
from secure_cloud_platform import (
    EnvironmentType,
    InstallationGuardrails,
    InstallationMode,
    InstallationProfile,
    InstallationStatus,
    PolicyDecision,
    PolicyViolation,
    merge_decisions,
    normalize_request,
)
from secure_cloud_platform.policies import evaluate_common_policies


def decision_codes(profile, request_model):
    resolved = normalize_request(profile, request_model)
    decision = evaluate_common_policies(profile, resolved, today=date(2026, 8, 8))
    return {item.code for item in decision.violations}


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("inactive", "installation-not-active"),
        ("region", "region-not-allowed"),
        ("budget", "budget-exceeds-maximum"),
        ("cluster", "cluster-size-not-allowed"),
        ("sandbox", "sandbox-production-forbidden"),
        ("expiry_missing", "nonproduction-expiry-required"),
        ("expiry_past", "nonproduction-expiry-not-future"),
        ("expiry_long", "nonproduction-expiry-too-long"),
    ],
)
def test_common_policy_denials(active_profile, request_model, change, expected) -> None:
    profile = active_profile
    request = request_model
    if change == "inactive":
        profile = InstallationProfile(
            installation_id="portfolio",
            provider=active_profile.provider,
            mode=active_profile.mode,
            status=InstallationStatus.DRAFT,
            guardrails=active_profile.guardrails,
        )
    elif change == "region":
        request = request_with(request_model, region="us-east-1")
    elif change == "budget":
        request = request_with(request_model, monthly_budget=Decimal("501"))
    elif change == "cluster":
        profile = InstallationProfile(
            installation_id="portfolio",
            provider=active_profile.provider,
            mode=active_profile.mode,
            status=active_profile.status,
            guardrails=InstallationGuardrails(
                allowed_regions=active_profile.guardrails.allowed_regions,
                budget_maximum=active_profile.guardrails.budget_maximum,
                max_nonproduction_lifetime_days=active_profile.guardrails.max_nonproduction_lifetime_days,
                allowed_cluster_sizes=("medium",),
            ),
        )
    elif change == "sandbox":
        profile = InstallationProfile(
            installation_id="portfolio",
            provider=active_profile.provider,
            mode=InstallationMode.SANDBOX,
            status=InstallationStatus.ACTIVE,
            guardrails=active_profile.guardrails,
        )
        request = request_with(
            request_model,
            environment=EnvironmentType.PRODUCTION,
            non_production_expiry=None,
        )
    elif change == "expiry_missing":
        request = request_with(request_model, non_production_expiry=None)
    elif change == "expiry_past":
        request = request_with(request_model, non_production_expiry=date(2026, 8, 7))
    elif change == "expiry_long":
        request = request_with(request_model, non_production_expiry=date(2026, 9, 20))
    assert expected in decision_codes(profile, request)


def test_provider_mismatch_is_denied(active_profile, request_model) -> None:
    azure_profile = InstallationProfile(
        installation_id="portfolio",
        provider="azure",
        mode=active_profile.mode,
        status=InstallationStatus.ACTIVE,
        guardrails=active_profile.guardrails,
    )
    resolved = normalize_request(azure_profile, request_model)
    decision = evaluate_common_policies(
        active_profile, resolved, today=date(2026, 8, 8)
    )
    assert not decision.allowed
    assert [item.code for item in decision.violations] == ["provider-mismatch"]


def test_production_does_not_require_expiry(active_profile, request_model) -> None:
    request = request_with(
        request_model,
        environment=EnvironmentType.PRODUCTION,
        non_production_expiry=None,
    )
    assert "nonproduction-expiry-required" not in decision_codes(
        active_profile, request
    )


def test_all_common_policies_allow_valid_request(active_profile, request_model) -> None:
    assert decision_codes(active_profile, request_model) == set()


@pytest.mark.parametrize("network_cidr", ["8.8.8.0/24", "2001:db8::/64"])
def test_public_and_ipv6_networks_are_policy_denials(
    active_profile, request_model, network_cidr
) -> None:
    request = request_with(request_model, network_cidr=network_cidr)
    assert "network-must-be-private-ipv4" in decision_codes(active_profile, request)


def test_policy_violations_are_sorted_and_deduplicated(
    active_profile, request_model
) -> None:
    request = request_with(
        request_model, region="us-east-1", monthly_budget=Decimal("501")
    )
    resolved = normalize_request(active_profile, request)
    decision = evaluate_common_policies(
        active_profile, resolved, today=date(2026, 8, 8)
    )
    assert [(item.code, item.field) for item in decision.violations] == [
        ("budget-exceeds-maximum", "monthly_budget"),
        ("region-not-allowed", "region"),
    ]


def test_merge_decisions_sorts_and_removes_exact_duplicates() -> None:
    region = PolicyViolation(code="region", message="Region denied", field="region")
    budget = PolicyViolation(code="budget", message="Budget denied", field="budget")
    merged = merge_decisions(
        PolicyDecision(allowed=False, violations=(region, budget)),
        PolicyDecision(allowed=False, violations=(region,)),
    )
    assert merged.allowed is False
    assert merged.violations == (budget, region)
