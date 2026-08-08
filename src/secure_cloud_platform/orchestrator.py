"""Provider-routed credential-free request evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from .adapters import ProviderAdapter
from .errors import AdapterProviderMismatchError, MissingProviderAdapterError
from .models import (
    CloudProvider,
    EnvironmentRequest,
    InstallationProfile,
    PolicyDecision,
    SimulationOutcome,
    SimulationResult,
)
from .normalization import normalize_request
from .policies import evaluate_common_policies, merge_decisions


class SimulationOrchestrator:
    """Evaluate requests with deterministic provider adapters.

    Every installation mode uses the same credential-free evaluation pipeline.
    Simulation is the only mode that represents a local simulation; sandbox and
    enterprise evaluation produces proposal inputs only.  The adapter port has
    no cloud execution operation, so this orchestrator cannot authenticate or
    change cloud state.
    """

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

    def evaluate(
        self,
        profile: InstallationProfile,
        request: EnvironmentRequest,
        *,
        today: date,
    ) -> SimulationOutcome:
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

    def simulate(
        self,
        profile: InstallationProfile,
        request: EnvironmentRequest,
        *,
        today: date,
    ) -> SimulationOutcome:
        """Backward-compatible name for deterministic local evaluation.

        The returned resources are descriptions only.  Sandbox and enterprise
        callers must still use the proposal workflow; this method never runs
        Terraform or contacts a cloud provider.
        """

        return self.evaluate(profile, request, today=today)
