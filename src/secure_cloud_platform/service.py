"""Shared application service for the API, CLI, and portal.

The service deliberately owns only process-local demo state.  It never reads
credentials or environment variables and never calls a cloud provider.  The
provider adapters registered here are simulation adapters implementing the
provider-neutral adapter port.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from threading import RLock
from typing import Final

from pydantic import Field, ValidationError

from .adapters import ProviderAdapter
from .errors import DomainError, SimulationModeRequiredError
from .models import (
    CloudProvider,
    DomainModel,
    EnvironmentRequest,
    InstallationGuardrails,
    InstallationMode,
    InstallationProfile,
    InstallationStatus,
    PolicyViolation,
    ResolvedEnvironmentRequest,
    SimulationOutcome,
)
from .normalization import normalize_request
from .orchestrator import SimulationOrchestrator
from .providers.aws import AWSSimulationAdapter
from .providers.azure import AzureSimulationAdapter

DEMO_TODAY: Final[date] = date(2026, 8, 8)


def _application_version() -> str:
    try:
        return version("secure-self-service-cloud-platform")
    except PackageNotFoundError:
        return "0.5.0"


APPLICATION_VERSION: Final[str] = _application_version()


class InterfaceError(DomainError):
    """Base class for expected, user-facing application failures."""


class ServiceConfigurationError(InterfaceError):
    """The application cannot construct a usable simulation service."""


class InstallationAlreadyExistsError(InterfaceError):
    """This process already owns its one installation profile."""


class InvalidInterfaceInputError(InterfaceError):
    """A transport input cannot form a valid immutable domain contract."""


class InstallationRejectedError(InterfaceError):
    """The selected provider rejected the installation configuration."""

    def __init__(self, validation: InstallationValidation) -> None:
        self.validation = validation
        super().__init__(
            "The installation cannot be activated until its configuration "
            "passes provider validation."
        )


class InstallationNotFoundError(InterfaceError):
    """No installation has been created in this process."""


class EnvironmentRequestNotFoundError(InterfaceError):
    """A request ID is not present in the process-local store."""


class IdempotencyKeyRequiredError(InterfaceError):
    """An environment request did not include an idempotency key."""


class IdempotencyConflictError(InterfaceError):
    """An idempotency key was reused for a different normalized payload."""


class UnsupportedSimulationError(InterfaceError):
    """The selected installation mode is not executable in this demo."""


class ServiceModel(DomainModel):
    """Immutable service response model base, kept separate from domain types."""


class ProviderDescriptor(ServiceModel):
    provider: CloudProvider
    display_name: str
    description: str
    available: bool = True


class ModeDescriptor(ServiceModel):
    mode: InstallationMode
    display_name: str
    description: str
    execution: str


class InstallationValidation(ServiceModel):
    allowed: bool
    violations: tuple[PolicyViolation, ...] = ()


class EnvironmentRequestRecord(ServiceModel):
    request: ResolvedEnvironmentRequest
    outcome: SimulationOutcome
    state: str = Field(pattern=r"^(accepted|denied)$")
    idempotency_key: str


def _default_adapters() -> dict[CloudProvider, ProviderAdapter]:
    """Register both required concrete simulation adapters."""

    return {
        CloudProvider.AWS: AWSSimulationAdapter(),
        CloudProvider.AZURE: AzureSimulationAdapter(),
    }


class PlatformService:
    """The sole application behavior shared by all local interfaces."""

    def __init__(
        self,
        adapters: Mapping[CloudProvider, ProviderAdapter] | None = None,
        *,
        today: date = DEMO_TODAY,
    ) -> None:
        self._today = today
        self._adapters = dict(_default_adapters() if adapters is None else adapters)
        self._orchestrator = SimulationOrchestrator(self._adapters)
        self._installation: InstallationProfile | None = None
        self._requests: dict[str, EnvironmentRequestRecord] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._lock = RLock()

    @property
    def today(self) -> date:
        return self._today

    def create_installation(
        self,
        *,
        installation_id: str = "default",
        provider: CloudProvider | str,
        mode: InstallationMode | str = InstallationMode.SIMULATION,
        guardrails: InstallationGuardrails | None = None,
    ) -> InstallationProfile:
        try:
            selected_provider = CloudProvider(provider)
        except ValueError as error:
            raise InvalidInterfaceInputError(
                "installation provider must be aws or azure"
            ) from error
        try:
            selected_mode = InstallationMode(mode)
        except ValueError as error:
            raise InvalidInterfaceInputError(
                "installation mode must be simulation, sandbox, or enterprise"
            ) from error
        if guardrails is None:
            default_regions = {
                CloudProvider.AWS: ("eu-west-1",),
                CloudProvider.AZURE: ("northeurope",),
            }
            guardrails = InstallationGuardrails(
                allowed_regions=default_regions[selected_provider]
            )
        try:
            profile = InstallationProfile(
                installation_id=installation_id,
                provider=selected_provider,
                mode=selected_mode,
                status=InstallationStatus.DRAFT,
                guardrails=guardrails,
            ).activate()
        except ValidationError as error:
            raise InvalidInterfaceInputError(
                "installation configuration contains invalid fields"
            ) from error
        with self._lock:
            if self._installation is not None:
                raise InstallationAlreadyExistsError(
                    "an installation already exists; provider selection is immutable"
                )
            validation = self._validate_profile(profile)
            if not validation.allowed:
                raise InstallationRejectedError(validation)
            self._installation = profile
            return profile

    def get_installation(self) -> InstallationProfile:
        with self._lock:
            if self._installation is None:
                raise InstallationNotFoundError(
                    "no installation exists; run setup init first"
                )
            return self._installation

    def validate_installation(
        self, profile: InstallationProfile | None = None
    ) -> InstallationValidation:
        candidate = profile or self.get_installation()
        return self._validate_profile(candidate)

    def _validate_profile(
        self, candidate: InstallationProfile
    ) -> InstallationValidation:
        if candidate.provider is None:
            return InstallationValidation(
                allowed=False,
                violations=(
                    PolicyViolation(
                        code="provider-required",
                        message="Select a provider before validating the installation.",
                        field="provider",
                    ),
                ),
            )
        adapter = self._adapter_for(candidate.provider)
        validation = adapter.validate_installation(candidate)
        return InstallationValidation(
            allowed=validation.allowed,
            violations=validation.violations,
        )

    def providers(self) -> tuple[ProviderDescriptor, ...]:
        return (
            ProviderDescriptor(
                provider=CloudProvider.AWS,
                display_name="Amazon Web Services",
                description="Credential-free AWS environment simulation.",
                available=(self._adapters.get(CloudProvider.AWS) is not None),
            ),
            ProviderDescriptor(
                provider=CloudProvider.AZURE,
                display_name="Microsoft Azure",
                description="Credential-free Azure environment simulation.",
                available=(self._adapters.get(CloudProvider.AZURE) is not None),
            ),
        )

    def modes(self) -> tuple[ModeDescriptor, ...]:
        return (
            ModeDescriptor(
                mode=InstallationMode.SIMULATION,
                display_name="Simulation",
                description="Deterministic, credential-free local demonstration.",
                execution="simulation-only",
            ),
            ModeDescriptor(
                mode=InstallationMode.SANDBOX,
                display_name="Sandbox",
                description="Describes a constrained future sandbox installation.",
                execution="not-enabled-in-demo",
            ),
            ModeDescriptor(
                mode=InstallationMode.ENTERPRISE,
                display_name="Enterprise",
                description="Describes a protected future enterprise installation.",
                execution="not-enabled-in-demo",
            ),
        )

    def evaluate_environment_request(
        self, request: EnvironmentRequest
    ) -> tuple[ResolvedEnvironmentRequest, SimulationOutcome]:
        profile = self.get_installation()
        try:
            outcome = self._orchestrator.simulate(profile, request, today=self._today)
        except SimulationModeRequiredError as error:
            raise UnsupportedSimulationError(str(error)) from error
        return normalize_request(profile, request), outcome

    def create_environment_request(
        self,
        request: EnvironmentRequest,
        *,
        idempotency_key: str | None,
    ) -> EnvironmentRequestRecord:
        key = idempotency_key.strip() if idempotency_key is not None else ""
        if not key:
            raise IdempotencyKeyRequiredError(
                "an Idempotency-Key is required for environment requests"
            )
        resolved, outcome = self.evaluate_environment_request(request)
        with self._lock:
            existing = self._idempotency.get(key)
            if existing is not None:
                existing_fingerprint, existing_request_id = existing
                if existing_fingerprint != resolved.fingerprint:
                    raise IdempotencyConflictError(
                        "Idempotency-Key was already used for a different request"
                    )
                return self._requests[existing_request_id]

            canonical = self._requests.get(resolved.request_id)
            if canonical is not None:
                self._idempotency[key] = (resolved.fingerprint, resolved.request_id)
                return canonical

            record = EnvironmentRequestRecord(
                request=resolved,
                outcome=outcome,
                state="accepted" if outcome.decision.allowed else "denied",
                idempotency_key=key,
            )
            self._requests[resolved.request_id] = record
            self._idempotency[key] = (resolved.fingerprint, resolved.request_id)
            return record

    def list_environment_requests(self) -> tuple[EnvironmentRequestRecord, ...]:
        with self._lock:
            return tuple(
                self._requests[request_id] for request_id in sorted(self._requests)
            )

    def get_environment_request(self, request_id: str) -> EnvironmentRequestRecord:
        with self._lock:
            try:
                return self._requests[request_id.strip().lower()]
            except KeyError as error:
                raise EnvironmentRequestNotFoundError(
                    f"environment request {request_id!r} was not found"
                ) from error

    def _adapter_for(self, provider: CloudProvider) -> ProviderAdapter:
        try:
            return self._adapters[provider]
        except KeyError as error:
            raise ServiceConfigurationError(
                f"no simulation adapter is registered for {provider.value}"
            ) from error

    def metrics(self) -> str:
        with self._lock:
            total = len(self._requests)
            accepted = sum(
                record.state == "accepted" for record in self._requests.values()
            )
            denied = total - accepted
            installation = int(self._installation is not None)
        return "\n".join(
            (
                "# TYPE platform_installation_present gauge",
                f"platform_installation_present {installation}",
                "# TYPE platform_environment_requests_total counter",
                f"platform_environment_requests_total {total}",
                "# TYPE platform_environment_requests_allowed_total counter",
                f"platform_environment_requests_allowed_total {accepted}",
                "# TYPE platform_environment_requests_denied_total counter",
                f"platform_environment_requests_denied_total {denied}",
                "",
            )
        )


__all__ = [
    "APPLICATION_VERSION",
    "DEMO_TODAY",
    "EnvironmentRequestNotFoundError",
    "EnvironmentRequestRecord",
    "IdempotencyConflictError",
    "IdempotencyKeyRequiredError",
    "InstallationAlreadyExistsError",
    "InstallationNotFoundError",
    "InstallationRejectedError",
    "InstallationValidation",
    "InterfaceError",
    "InvalidInterfaceInputError",
    "ModeDescriptor",
    "PlatformService",
    "ProviderDescriptor",
    "ServiceConfigurationError",
    "UnsupportedSimulationError",
]
