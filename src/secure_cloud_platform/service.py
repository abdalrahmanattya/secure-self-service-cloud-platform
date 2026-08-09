"""Shared application service for the API, CLI, and portal.

The service deliberately owns only process-local demo state.  It never reads
credentials or environment variables and never calls a cloud provider.  The
provider adapters registered here are deterministic, credential-free adapters
implementing the provider-neutral adapter port.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from threading import RLock
from typing import Final

from pydantic import Field, ValidationError

from .adapters import ProviderAdapter
from .errors import DomainError
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
from .proposals import (
    DeploymentProposal,
    ProposalInputError,
    build_deployment_proposal,
)
from .providers.aws import AWSSimulationAdapter
from .providers.azure import AzureSimulationAdapter

DEMO_TODAY: Final[date] = date(2026, 8, 8)


APPLICATION_VERSION: Final[str] = "1.0.0"


class InterfaceError(DomainError):
    """Base class for expected, user-facing application failures."""


class ServiceConfigurationError(InterfaceError):
    """The application cannot construct a usable credential-free service."""


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


class ProposalNotFoundError(InterfaceError):
    """A proposal ID is not present in the process-local store."""


class ProposalNotAllowedError(InterfaceError):
    """A denied request cannot be converted into a deployment proposal."""


class IdempotencyKeyRequiredError(InterfaceError):
    """An environment request did not include an idempotency key."""


class IdempotencyConflictError(InterfaceError):
    """An idempotency key was reused for a different normalized payload."""


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
        self._proposals: dict[str, DeploymentProposal] = {}
        self._proposal_idempotency: dict[str, tuple[str, str]] = {}
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
                description=(
                    "Credential-free AWS request evaluation and proposal inputs."
                ),
                available=(self._adapters.get(CloudProvider.AWS) is not None),
            ),
            ProviderDescriptor(
                provider=CloudProvider.AZURE,
                display_name="Microsoft Azure",
                description=(
                    "Credential-free Azure request evaluation and proposal inputs."
                ),
                available=(self._adapters.get(CloudProvider.AZURE) is not None),
            ),
        )

    def modes(self) -> tuple[ModeDescriptor, ...]:
        return (
            ModeDescriptor(
                mode=InstallationMode.SIMULATION,
                display_name="Simulation",
                description=(
                    "Deterministic, credential-free local evaluation and "
                    "resource simulation; no deployment is performed."
                ),
                execution="simulation-only",
            ),
            ModeDescriptor(
                mode=InstallationMode.SANDBOX,
                display_name="Sandbox",
                description=(
                    "Deterministic, credential-free proposal for a constrained "
                    "sandbox deployment; cloud execution remains protected."
                ),
                execution="proposal-only",
            ),
            ModeDescriptor(
                mode=InstallationMode.ENTERPRISE,
                display_name="Enterprise",
                description=(
                    "Deterministic, credential-free proposal for a protected "
                    "enterprise deployment; cloud execution remains protected."
                ),
                execution="proposal-only",
            ),
        )

    def evaluate_environment_request(
        self, request: EnvironmentRequest
    ) -> tuple[ResolvedEnvironmentRequest, SimulationOutcome]:
        profile = self.get_installation()
        outcome = self._orchestrator.evaluate(profile, request, today=self._today)
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

    def create_deployment_proposal(
        self,
        request_id: str,
        *,
        idempotency_key: str | None,
    ) -> DeploymentProposal:
        """Create or retrieve a deterministic proposal for an accepted request.

        The complete lookup, build, and insertion operation is protected by
        the service lock.  This makes concurrent retries converge on one
        immutable proposal without introducing timestamps or random IDs.
        """

        key = idempotency_key.strip() if idempotency_key is not None else ""
        if not key:
            raise IdempotencyKeyRequiredError(
                "an Idempotency-Key is required for deployment proposals"
            )
        normalized_request_id = request_id.strip().lower()
        with self._lock:
            try:
                record = self._requests[normalized_request_id]
            except KeyError as error:
                raise EnvironmentRequestNotFoundError(
                    f"environment request {request_id!r} was not found"
                ) from error
            if record.state != "accepted":
                raise ProposalNotAllowedError(
                    "denied environment requests cannot produce proposals"
                )
            profile = self._installation
            if profile is None:
                raise InstallationNotFoundError(
                    "no installation exists; run setup init first"
                )
            try:
                proposal = build_deployment_proposal(
                    record.request,
                    record.outcome,
                    profile,
                )
            except ProposalInputError as error:
                raise ProposalNotAllowedError(str(error)) from error
            existing = self._proposal_idempotency.get(key)
            if existing is not None:
                existing_request_id, existing_proposal_id = existing
                if existing_request_id != normalized_request_id:
                    raise IdempotencyConflictError(
                        "Idempotency-Key was already used for a different request"
                    )
                return self._proposals[existing_proposal_id]

            canonical = self._proposals.get(proposal.proposal_id)
            if canonical is None:
                self._proposals[proposal.proposal_id] = proposal
                canonical = proposal
            self._proposal_idempotency[key] = (
                normalized_request_id,
                canonical.proposal_id,
            )
            return canonical

    def list_deployment_proposals(self) -> tuple[DeploymentProposal, ...]:
        """List proposals in stable proposal-ID order."""

        with self._lock:
            return tuple(
                self._proposals[proposal_id] for proposal_id in sorted(self._proposals)
            )

    def get_deployment_proposal(self, proposal_id: str) -> DeploymentProposal:
        """Get one process-local immutable proposal by ID."""

        with self._lock:
            try:
                return self._proposals[proposal_id.strip().lower()]
            except KeyError as error:
                raise ProposalNotFoundError(
                    f"deployment proposal {proposal_id!r} was not found"
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
            proposals = len(self._proposals)
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
                "# TYPE platform_deployment_proposals_total gauge",
                f"platform_deployment_proposals_total {proposals}",
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
    "ProposalNotAllowedError",
    "ProposalNotFoundError",
    "ProviderDescriptor",
    "ServiceConfigurationError",
]
