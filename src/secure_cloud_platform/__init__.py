"""Provider-neutral domain contracts for the self-service cloud platform."""

from .adapters import (
    AWSProviderAdapter,
    AzureProviderAdapter,
    ProviderAdapter,
)
from .errors import (
    AdapterProviderMismatchError,
    DomainError,
    InstallationConfigurationError,
    InvalidLifecycleTransitionError,
    MissingProviderAdapterError,
    ProviderLockedError,
    SimulationModeRequiredError,
)
from .models import (
    CloudProvider,
    ClusterSize,
    DataClassification,
    EnvironmentRequest,
    EnvironmentType,
    InstallationGuardrails,
    InstallationMode,
    InstallationProfile,
    InstallationStatus,
    PolicyDecision,
    PolicyViolation,
    ProviderValidation,
    ResolvedEnvironmentRequest,
    SimulationOutcome,
    SimulationResource,
    SimulationResult,
)
from .normalization import normalize_request
from .orchestrator import SimulationOrchestrator
from .policies import evaluate_common_policies, merge_decisions

__all__ = [
    "AWSProviderAdapter",
    "AdapterProviderMismatchError",
    "AzureProviderAdapter",
    "CloudProvider",
    "ClusterSize",
    "DataClassification",
    "DomainError",
    "EnvironmentRequest",
    "EnvironmentType",
    "InstallationConfigurationError",
    "InstallationGuardrails",
    "InstallationMode",
    "InstallationProfile",
    "InstallationStatus",
    "InvalidLifecycleTransitionError",
    "MissingProviderAdapterError",
    "PolicyDecision",
    "PolicyViolation",
    "ProviderAdapter",
    "ProviderLockedError",
    "ProviderValidation",
    "ResolvedEnvironmentRequest",
    "SimulationModeRequiredError",
    "SimulationOrchestrator",
    "SimulationOutcome",
    "SimulationResource",
    "SimulationResult",
    "evaluate_common_policies",
    "merge_decisions",
    "normalize_request",
]
