"""Typed errors raised by the provider-neutral domain."""


class DomainError(Exception):
    """Base class for expected domain failures."""


class InstallationConfigurationError(DomainError):
    """The installation profile cannot resolve a provider or valid setup."""


class ProviderLockedError(DomainError):
    """An attempt was made to change a provider after activation."""


class InvalidLifecycleTransitionError(DomainError):
    """An installation status transition is not permitted."""


class MissingProviderAdapterError(DomainError):
    """No adapter is registered for the selected provider."""


class AdapterProviderMismatchError(DomainError):
    """An adapter registry key does not match the adapter declaration."""
