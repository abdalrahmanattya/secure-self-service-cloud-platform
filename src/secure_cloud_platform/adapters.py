"""Provider adapter ports with no provider SDK dependency."""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from .models import (
    CloudProvider,
    InstallationProfile,
    ProviderValidation,
    ResolvedEnvironmentRequest,
    SimulationResource,
)


@runtime_checkable
class ProviderAdapter(Protocol):
    """Port implemented by a provider-specific simulation or runtime adapter."""

    @property
    def provider(self) -> CloudProvider:
        """Provider implemented by this adapter."""

    def validate_installation(self, profile: InstallationProfile) -> ProviderValidation:
        """Validate provider-specific installation configuration."""

    def validate_request(
        self, request: ResolvedEnvironmentRequest
    ) -> ProviderValidation:
        """Validate provider-specific request constraints."""

    def simulate(
        self, request: ResolvedEnvironmentRequest
    ) -> tuple[SimulationResource, ...]:
        """Return deterministic resource descriptions without cloud calls."""


class AWSProviderAdapter(ProviderAdapter, Protocol):
    """Explicit adapter port for an AWS installation."""

    @property
    def provider(self) -> Literal[CloudProvider.AWS]:
        """AWS provider marker for static type checking."""


class AzureProviderAdapter(ProviderAdapter, Protocol):
    """Explicit adapter port for an Azure installation."""

    @property
    def provider(self) -> Literal[CloudProvider.AZURE]:
        """Azure provider marker for static type checking."""
