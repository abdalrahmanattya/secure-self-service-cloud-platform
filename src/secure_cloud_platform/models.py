"""Immutable, provider-neutral domain models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyNetwork,
    field_validator,
    model_validator,
)

from .errors import (
    InstallationConfigurationError,
    InvalidLifecycleTransitionError,
    ProviderLockedError,
)


class CloudProvider(StrEnum):
    AWS = "aws"
    AZURE = "azure"


class InstallationMode(StrEnum):
    SIMULATION = "simulation"
    SANDBOX = "sandbox"
    ENTERPRISE = "enterprise"


class InstallationStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class EnvironmentType(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ClusterSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class DomainModel(BaseModel):
    """Base model enforcing immutable, explicit contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class InstallationGuardrails(DomainModel):
    """Common limits applied before a provider adapter is consulted."""

    allowed_regions: tuple[str, ...] = ("example-region",)
    budget_maximum: Decimal = Decimal("1000.00")
    max_nonproduction_lifetime_days: int = Field(default=30, ge=1, le=3650)
    allowed_cluster_sizes: tuple[ClusterSize, ...] = (
        ClusterSize.SMALL,
        ClusterSize.MEDIUM,
        ClusterSize.LARGE,
    )

    @field_validator("allowed_regions")
    @classmethod
    def validate_regions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted({item.strip().lower() for item in value}))
        if not normalized or any(not item for item in normalized):
            raise ValueError("allowed_regions must contain non-empty region names")
        return normalized

    @field_validator("budget_maximum")
    @classmethod
    def validate_budget(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("budget_maximum must be positive")
        return value.quantize(Decimal("0.01"))

    @field_validator("allowed_cluster_sizes")
    @classmethod
    def validate_cluster_sizes(
        cls, value: tuple[ClusterSize, ...]
    ) -> tuple[ClusterSize, ...]:
        normalized = tuple(sorted(set(value), key=lambda item: item.value))
        if not normalized:
            raise ValueError("allowed_cluster_sizes must not be empty")
        return normalized


class InstallationProfile(DomainModel):
    """Provider and lifecycle configuration for one installation."""

    installation_id: str = Field(min_length=1)
    provider: CloudProvider | None = None
    mode: InstallationMode = InstallationMode.SIMULATION
    status: InstallationStatus = InstallationStatus.DRAFT
    guardrails: InstallationGuardrails = Field(default_factory=InstallationGuardrails)

    @field_validator("installation_id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("installation_id must not be empty")
        return normalized

    @model_validator(mode="after")
    def require_provider_for_non_draft(self) -> Self:
        if self.status is not InstallationStatus.DRAFT and self.provider is None:
            raise ValueError("active and retired installations require a provider")
        return self

    def _validated_copy(self, **updates: Any) -> Self:
        values = self.model_dump()
        values.update(updates)
        return type(self).model_validate(values)

    def with_provider(self, provider: CloudProvider | str) -> Self:
        if self.status is not InstallationStatus.DRAFT:
            raise ProviderLockedError(
                "provider is locked after installation activation"
            )
        return self._validated_copy(provider=provider)

    def activate(self) -> Self:
        if self.status is not InstallationStatus.DRAFT:
            raise InvalidLifecycleTransitionError(
                f"cannot activate installation from {self.status.value}"
            )
        if self.provider is None:
            raise InstallationConfigurationError(
                "a provider must be selected before activation"
            )
        return self._validated_copy(status=InstallationStatus.ACTIVE)

    def retire(self) -> Self:
        if self.status is not InstallationStatus.ACTIVE:
            raise InvalidLifecycleTransitionError(
                f"cannot retire installation from {self.status.value}"
            )
        return self._validated_copy(status=InstallationStatus.RETIRED)


class EnvironmentRequest(DomainModel):
    """Raw request submitted by a user; deliberately contains no provider."""

    application: str = Field(min_length=1)
    environment: EnvironmentType
    owner: str = Field(min_length=1)
    cost_centre: str = Field(min_length=1)
    data_classification: DataClassification
    region: str = Field(min_length=1)
    network_cidr: IPvAnyNetwork
    cluster_size: ClusterSize
    monthly_budget: Decimal = Field(gt=0)
    business_justification: str = Field(min_length=1)
    non_production_expiry: date | None = None

    @field_validator(
        "application", "owner", "cost_centre", "region", "business_justification"
    )
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("text fields must not be empty")
        return normalized

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str) -> str:
        return value.lower()

    @field_validator("monthly_budget")
    @classmethod
    def normalize_money(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))


class ResolvedEnvironmentRequest(EnvironmentRequest):
    """Normalized request with the provider resolved from the profile."""

    provider: CloudProvider
    canonical_json: str = Field(min_length=1)
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_id: str = Field(pattern=r"^env-[0-9a-f]{16}$")


class PolicyViolation(DomainModel):
    """Stable, user-facing explanation of one failed policy."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    field: str = Field(min_length=1)


def _canonicalize_violations(value: Any) -> tuple[PolicyViolation, ...]:
    violations = tuple(
        item
        if isinstance(item, PolicyViolation)
        else PolicyViolation.model_validate(item)
        for item in value
    )
    unique = {(item.code, item.field, item.message): item for item in violations}
    return tuple(
        unique[key]
        for key in sorted(unique, key=lambda item: (item[0], item[1], item[2]))
    )


class PolicyDecision(DomainModel):
    """Deterministic aggregate policy result."""

    allowed: bool
    violations: tuple[PolicyViolation, ...] = ()

    @field_validator("violations", mode="before")
    @classmethod
    def canonicalize_violations(cls, value: Any) -> tuple[PolicyViolation, ...]:
        return _canonicalize_violations(value)

    @model_validator(mode="after")
    def require_consistent_result(self) -> Self:
        if self.allowed and self.violations:
            raise ValueError("an allowed decision cannot contain violations")
        if not self.allowed and not self.violations:
            raise ValueError("a denied decision must contain at least one violation")
        return self


class ProviderValidation(DomainModel):
    """Provider adapter policy result without provider-native details."""

    allowed: bool
    violations: tuple[PolicyViolation, ...] = ()

    @field_validator("violations", mode="before")
    @classmethod
    def canonicalize_violations(cls, value: Any) -> tuple[PolicyViolation, ...]:
        return _canonicalize_violations(value)

    @model_validator(mode="after")
    def require_consistent_result(self) -> Self:
        if self.allowed and self.violations:
            raise ValueError("an allowed validation cannot contain violations")
        if not self.allowed and not self.violations:
            raise ValueError("a denied validation must contain at least one violation")
        return self


class SimulationResource(DomainModel):
    """Stable description of a resource that would be proposed."""

    kind: str = Field(min_length=1)
    name: str = Field(min_length=1)
    attributes: tuple[tuple[str, str], ...] = ()

    @field_validator("attributes")
    @classmethod
    def canonicalize_attributes(
        cls, value: tuple[tuple[str, str], ...]
    ) -> tuple[tuple[str, str], ...]:
        keys = [key for key, _ in value]
        if len(keys) != len(set(keys)):
            raise ValueError("simulation resource attribute keys must be unique")
        return tuple(sorted(value, key=lambda item: item[0]))


class SimulationResult(DomainModel):
    """Credential-free simulation output."""

    provider: CloudProvider
    request_id: str = Field(pattern=r"^env-[0-9a-f]{16}$")
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    resources: tuple[SimulationResource, ...]

    @field_validator("resources")
    @classmethod
    def sort_resources(
        cls, value: tuple[SimulationResource, ...]
    ) -> tuple[SimulationResource, ...]:
        return tuple(
            sorted(
                value,
                key=lambda item: (item.kind, item.name, item.attributes),
            )
        )


class SimulationOutcome(DomainModel):
    """Policy decision plus optional deterministic simulation result."""

    decision: PolicyDecision
    result: SimulationResult | None = None

    @model_validator(mode="after")
    def require_result_matches_decision(self) -> Self:
        if self.decision.allowed != (self.result is not None):
            raise ValueError("simulation result must exist exactly when allowed")
        return self
