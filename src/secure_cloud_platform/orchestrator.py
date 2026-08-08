"""Provider-routed credential-free simulation orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from .adapters import ProviderAdapter
from .errors import (
    AdapterProviderMismatchError,
    MissingProviderAdapterError,
    SimulationModeRequiredError,
)
from .models import (
    CloudProvider,
    EnvironmentRequest,
    InstallationMode,
    InstallationProfile,
    PolicyDecision,
    SimulationOutcome,
    SimulationResult,
)
from .normalization import normalize_request
from .policies import evaluate_common_policies, merge_decisions


class SimulationOrchestrator:
    """Coordinate common policy, one selected adapter, and simulation output."""

    def __init__(self, adapters: Mapping[CloudProvider, ProviderAdapter]) -> None:
        self._adapters = dict(adapters)
        for declared_provider, adapter in self._adapters.items():
            if not isinstance(declared_provider, CloudProvider):
                raise AdapterProviderMismatchError(
                    "adapter registry keys must be CloudProvider values"
                )
            if not isinstance(adapter, ProviderAdapter):
                raise TypeError("adapter does not implement ProviderAdapter")
            if not isinstance(adapter.provider, CloudProvider) or (
                adapter.provider is not declared_provider
            ):
                raise AdapterProviderMismatchError(
                    f"adapter provider does not match registry key "
                    f"{declared_provider.value}"
                )

    def simulate(
        self,
        profile: InstallationProfile,
        request: EnvironmentRequest,
        *,
        today: date,
    ) -> SimulationOutcome:
        if profile.mode is not InstallationMode.SIMULATION:
            raise SimulationModeRequiredError(
                "credential-free simulation requires simulation installation mode"
            )

        resolved = normalize_request(profile, request)
        common = evaluate_common_policies(profile, resolved, today=today)
        if not common.allowed:
            return SimulationOutcome(decision=common)
        if profile.provider is None:
            raise MissingProviderAdapterError("installation has no selected provider")
        try:
            adapter = self._adapters[profile.provider]
        except KeyError as error:
            raise MissingProviderAdapterError(
                f"no adapter is registered for {profile.provider.value}"
            ) from error

        installation_validation = adapter.validate_installation(profile)
        installation_decision = PolicyDecision(
            allowed=installation_validation.allowed,
            violations=installation_validation.violations,
        )
        decision = merge_decisions(common, installation_decision)
        if not decision.allowed:
            return SimulationOutcome(decision=decision)
        request_validation = adapter.validate_request(resolved)
        request_decision = PolicyDecision(
            allowed=request_validation.allowed,
            violations=request_validation.violations,
        )
        decision = merge_decisions(decision, request_decision)
        if not decision.allowed:
            return SimulationOutcome(decision=decision)
        result = SimulationResult(
            provider=resolved.provider,
            request_id=resolved.request_id,
            fingerprint=resolved.fingerprint,
            resources=adapter.simulate(resolved),
        )
        return SimulationOutcome(decision=decision, result=result)
