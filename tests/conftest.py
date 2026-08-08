from datetime import date
from decimal import Decimal

import pytest

from secure_cloud_platform import (
    CloudProvider,
    ClusterSize,
    DataClassification,
    EnvironmentRequest,
    EnvironmentType,
    InstallationGuardrails,
    InstallationMode,
    InstallationProfile,
    InstallationStatus,
)

TODAY = date(2026, 8, 8)


@pytest.fixture
def request_model() -> EnvironmentRequest:
    return EnvironmentRequest(
        application="payments-api",
        environment=EnvironmentType.DEVELOPMENT,
        owner="Platform Team",
        cost_centre="FIN-042",
        data_classification=DataClassification.INTERNAL,
        region="EU-WEST-1",
        network_cidr="10.42.0.0/16",
        cluster_size=ClusterSize.SMALL,
        monthly_budget=Decimal("250"),
        business_justification=" Standard development environment ",
        non_production_expiry=date(2026, 8, 20),
    )


@pytest.fixture
def active_profile() -> InstallationProfile:
    return InstallationProfile(
        installation_id="portfolio",
        provider=CloudProvider.AWS,
        mode=InstallationMode.SIMULATION,
        status=InstallationStatus.ACTIVE,
        guardrails=InstallationGuardrails(
            allowed_regions=("eu-west-1",),
            budget_maximum=Decimal("500.00"),
            max_nonproduction_lifetime_days=30,
        ),
    )


@pytest.fixture
def profile_factory():
    def factory(
        provider: CloudProvider = CloudProvider.AWS,
        *,
        mode: InstallationMode = InstallationMode.SIMULATION,
        status: InstallationStatus = InstallationStatus.ACTIVE,
        guardrails: InstallationGuardrails | None = None,
    ) -> InstallationProfile:
        return InstallationProfile(
            installation_id="portfolio",
            provider=provider,
            mode=mode,
            status=status,
            guardrails=guardrails
            or InstallationGuardrails(
                allowed_regions=("eu-west-1", "northeurope"),
                budget_maximum=Decimal("500.00"),
                max_nonproduction_lifetime_days=30,
            ),
        )

    return factory


def request_with(
    request_model: EnvironmentRequest, **updates: object
) -> EnvironmentRequest:
    values = request_model.model_dump()
    values.update(updates)
    return EnvironmentRequest(**values)
