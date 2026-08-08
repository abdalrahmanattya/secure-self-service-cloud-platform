"""Deterministic normalization and identity for environment requests."""

from __future__ import annotations

import hashlib
import json

from .errors import InstallationConfigurationError
from .models import (
    EnvironmentRequest,
    InstallationProfile,
    ResolvedEnvironmentRequest,
)


def normalize_request(
    profile: InstallationProfile, request: EnvironmentRequest
) -> ResolvedEnvironmentRequest:
    """Resolve a request against the selected installation provider.

    The profile may still be draft so policy evaluation can report the typed
    inactive-installation denial. Provider selection is nevertheless required.
    """

    if profile.provider is None:
        raise InstallationConfigurationError("installation has no selected provider")

    values = request.model_dump()
    values["provider"] = profile.provider
    provisional = ResolvedEnvironmentRequest(
        **values,
        canonical_json="pending",
        fingerprint="0" * 64,
        request_id="env-" + "0" * 16,
    )
    canonical_values = provisional.model_dump(mode="json")
    canonical_values.pop("canonical_json")
    canonical_values.pop("fingerprint")
    canonical_values.pop("request_id")
    canonical_json = json.dumps(
        canonical_values,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    fingerprint = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return ResolvedEnvironmentRequest(
        **canonical_values,
        canonical_json=canonical_json,
        fingerprint=fingerprint,
        request_id=f"env-{fingerprint[:16]}",
    )
