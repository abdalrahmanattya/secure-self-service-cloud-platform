"""Deterministic, credential-free deployment proposal contracts.

Proposal construction is deliberately a pure transformation of an accepted
request, its simulation result, and the selected installation profile.  This
module has no filesystem, network, cloud, or clock access.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from decimal import Decimal
from enum import StrEnum
from typing import Final

import yaml
from pydantic import Field, field_validator

from .models import (
    CloudProvider,
    ClusterSize,
    DomainModel,
    InstallationMode,
    InstallationProfile,
    PolicyDecision,
    ResolvedEnvironmentRequest,
    SimulationOutcome,
)

PROPOSAL_SCHEMA_VERSION: Final[str] = "proposal.v1"
BUNDLE_MARKER_FILENAME: Final[str] = ".platform-proposal.json"
_SAFE_RELATIVE_PATH = re.compile(r"[A-Za-z0-9._/-]+")


def _stable_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


class ProposalArtifact(DomainModel):
    """One textual file in a proposal bundle."""

    relative_path: str = Field(min_length=1)
    content: str

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        segments = value.split("/")
        if (
            value.startswith("/")
            or "\\" in value
            or not _SAFE_RELATIVE_PATH.fullmatch(value)
            or any(segment in {"", ".", ".."} for segment in segments)
        ):
            raise ValueError("artifact paths must be normalized relative paths")
        return value


class ProposalState(StrEnum):
    """The only truthful state the local, review-only service can claim."""

    READY_FOR_REVIEW = "ready_for_review"


class DeploymentProposal(DomainModel):
    """Immutable proposal metadata and its complete textual artifact bundle."""

    schema_version: str = PROPOSAL_SCHEMA_VERSION
    proposal_id: str = Field(pattern=r"^proposal-[0-9a-f]{16}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_id: str = Field(pattern=r"^env-[0-9a-f]{16}$")
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    installation_id: str = Field(min_length=1)
    provider: CloudProvider
    mode: InstallationMode
    state: ProposalState = ProposalState.READY_FOR_REVIEW
    artifacts: tuple[ProposalArtifact, ...] = Field(min_length=5)

    @field_validator("artifacts")
    @classmethod
    def sort_and_validate_artifacts(
        cls, value: tuple[ProposalArtifact, ...]
    ) -> tuple[ProposalArtifact, ...]:
        paths = [artifact.relative_path for artifact in value]
        if len(paths) != len(set(paths)):
            raise ValueError("proposal artifact paths must be unique")
        return tuple(sorted(value, key=lambda artifact: artifact.relative_path))

    @property
    def artifact_paths(self) -> tuple[str, ...]:
        """Return stable artifact paths without changing serialized state."""

        return tuple(artifact.relative_path for artifact in self.artifacts)


class ProposalBundleMarker(DomainModel):
    """Small allowlist marker required before an existing bundle is replaced."""

    schema_version: str = PROPOSAL_SCHEMA_VERSION
    proposal_id: str = Field(pattern=r"^proposal-[0-9a-f]{16}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_paths: tuple[str, ...] = Field(min_length=1)

    @field_validator("artifact_paths")
    @classmethod
    def validate_artifact_paths(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("bundle marker artifact paths must be unique")
        if BUNDLE_MARKER_FILENAME in value:
            raise ValueError("bundle marker cannot declare itself as an artifact")
        if tuple(sorted(value)) != value:
            raise ValueError("bundle marker artifact paths must be sorted")
        for path in value:
            ProposalArtifact(relative_path=path, content="")
        return value


class ProposalInputError(ValueError):
    """Proposal inputs cannot safely form the selected Terraform contract."""


def _request_document(request: ResolvedEnvironmentRequest) -> dict[str, object]:
    document = request.model_dump(mode="json")
    document.pop("canonical_json", None)
    return {str(key): value for key, value in document.items()}


def _yaml_content(document: dict[str, object]) -> str:
    return yaml.safe_dump(
        document,
        allow_unicode=False,
        default_flow_style=False,
        sort_keys=True,
    )


def _policy_content(decision: PolicyDecision) -> str:
    decision_text = "allowed" if decision.allowed else "denied"
    lines = ["# Policy summary", "", f"Decision: {decision_text}", ""]
    if decision.allowed:
        lines.append("No policy violations were reported.")
    else:
        lines.append("Violations:")
        lines.extend(
            f"- `{violation.code}` ({violation.field}): {violation.message}"
            for violation in decision.violations
        )
    return "\n".join(lines) + "\n"


def _terraform_document(
    request: ResolvedEnvironmentRequest,
    profile: InstallationProfile,
    outcome: SimulationOutcome,
) -> dict[str, object]:
    result = outcome.result
    if result is None:
        raise ValueError("an accepted request must have a simulation result")
    if profile.provider is None:
        raise ValueError("an active proposal installation must select a provider")
    resources = [
        {
            "attributes": {key: value for key, value in resource.attributes},
            "kind": resource.kind,
            "name": resource.name,
        }
        for resource in result.resources
    ]
    return {
        "environment": _request_document(request),
        "installation_mode": profile.mode.value,
        "provider": profile.provider.value,
        "resources": resources,
    }


def _safe_name_prefix(request: ResolvedEnvironmentRequest) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", request.application.lower()).strip("-")
    slug = slug[:24].strip("-") or "application"
    return f"scp-{slug}-{request.request_id}"


def _allocate_subnets(cidr: str, count: int) -> tuple[str, ...]:
    """Allocate deterministic, non-overlapping IPv4 subnets from a request CIDR."""

    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as error:
        raise ProposalInputError("the request CIDR cannot be parsed") from error
    if not isinstance(network, ipaddress.IPv4Network):
        raise ProposalInputError(
            "the request CIDR must provide IPv4 subnets for Terraform inputs"
        )
    required_bits = (count - 1).bit_length()
    subnet_prefix = max(network.prefixlen + required_bits, 24)
    if subnet_prefix > 28 or subnet_prefix > network.max_prefixlen:
        raise ProposalInputError(
            "the request CIDR cannot supply the required private and public subnets"
        )
    subnets = tuple(network.subnets(new_prefix=subnet_prefix))
    if len(subnets) < count:
        raise ProposalInputError(
            "the request CIDR cannot supply the required private and public subnets"
        )
    return tuple(str(subnet) for subnet in subnets[:count])


def _money_number(value: Decimal) -> int | float:
    normalized = value.quantize(Decimal("0.01"))
    if normalized == normalized.to_integral_value():
        return int(normalized)
    return float(normalized)


def _terraform_variables(
    request: ResolvedEnvironmentRequest,
    profile: InstallationProfile,
) -> dict[str, object]:
    """Return only safe, request-derived variables accepted by each root stack."""

    name_prefix = _safe_name_prefix(request)
    if request.provider is CloudProvider.AWS:
        subnets = _allocate_subnets(str(request.network_cidr), 4)
        return {
            "desired_nodes": {
                ClusterSize.SMALL: 2,
                ClusterSize.MEDIUM: 3,
                ClusterSize.LARGE: 5,
            }[request.cluster_size],
            "mode": profile.mode.value,
            "monthly_budget_usd": _money_number(request.monthly_budget),
            "name_prefix": name_prefix,
            "private_subnet_cidrs": list(subnets[:2]),
            "public_subnet_cidrs": list(subnets[2:]),
            "region": request.region,
            "vpc_cidr": str(request.network_cidr),
        }
    subnets = _allocate_subnets(str(request.network_cidr), 2)
    return {
        "desired_nodes": {
            ClusterSize.SMALL: 2,
            ClusterSize.MEDIUM: 3,
            ClusterSize.LARGE: 5,
        }[request.cluster_size],
        "location": request.region,
        "mode": profile.mode.value,
        "monthly_budget_eur": _money_number(request.monthly_budget),
        "name_prefix": name_prefix,
        "private_subnet_prefixes": list(subnets),
        "vnet_address_space": [str(request.network_cidr)],
    }


def _proposal_identity(
    request: ResolvedEnvironmentRequest,
    profile: InstallationProfile,
) -> dict[str, object]:
    if profile.provider is None:
        raise ValueError("an active proposal installation must select a provider")
    return {
        "installation_id": profile.installation_id,
        "mode": profile.mode.value,
        "provider": profile.provider.value,
        "proposal_schema_version": PROPOSAL_SCHEMA_VERSION,
        "request": json.loads(request.canonical_json),
    }


def _proposal_identity_document(
    request: ResolvedEnvironmentRequest,
    profile: InstallationProfile,
    proposal_id: str,
) -> dict[str, object]:
    """Return workflow-safe proposal identity without self-referential hash data."""

    if profile.provider is None:
        raise ValueError("an active proposal installation must select a provider")
    return {
        "installation_id": profile.installation_id,
        "mode": profile.mode.value,
        "proposal_id": proposal_id,
        "provider": profile.provider.value,
        "request_fingerprint": request.fingerprint,
        "request_id": request.request_id,
        "schema_version": PROPOSAL_SCHEMA_VERSION,
        "state": ProposalState.READY_FOR_REVIEW.value,
    }


def build_deployment_proposal(
    request: ResolvedEnvironmentRequest,
    outcome: SimulationOutcome,
    profile: InstallationProfile,
) -> DeploymentProposal:
    """Build the canonical proposal for one accepted normalized request."""

    if not outcome.decision.allowed or outcome.result is None:
        raise ValueError("denied requests cannot produce deployment proposals")
    if profile.provider is None or profile.provider is not request.provider:
        raise ValueError("proposal provider must match the selected installation")
    provider = profile.provider

    identity = _proposal_identity(request, profile)
    identity_json = _stable_json(identity)
    proposal_id = f"proposal-{hashlib.sha256(identity_json.encode()).hexdigest()[:16]}"
    request_document = _request_document(request)
    proposal_identity_document = _proposal_identity_document(
        request,
        profile,
        proposal_id,
    )
    terraform_document = _terraform_document(request, profile, outcome)
    terraform_variables = _terraform_variables(request, profile)
    terraform_json = (
        json.dumps(
            terraform_document,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    request_json = (
        json.dumps(
            request_document,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    terraform_variables_json = (
        json.dumps(
            terraform_variables,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    proposal_identity_json = (
        json.dumps(
            proposal_identity_document,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    artifacts: tuple[ProposalArtifact, ...] = (
        ProposalArtifact(
            relative_path=f"environments/policies/{request.request_id}.md",
            content=_policy_content(outcome.decision),
        ),
        ProposalArtifact(
            relative_path=f"environments/proposals/{proposal_id}.md",
            content=(
                f"# Deployment proposal {proposal_id}\n\n"
                "## Summary\n\n"
                f"- Request: `{request.request_id}`\n"
                f"- Provider: `{request.provider.value}`\n"
                f"- Installation mode: `{profile.mode.value}`\n"
                "- Execution: protected review and deployment workflows only\n\n"
                "## Artifacts\n\n"
                "The accompanying files are deterministic proposal inputs; no "
                "credentials, timestamps, or cloud identifiers are included.\n"
            ),
        ),
        ProposalArtifact(
            relative_path=f"environments/proposals/{proposal_id}.json",
            content=proposal_identity_json,
        ),
        ProposalArtifact(
            relative_path=f"environments/requests/{request.request_id}.json",
            content=request_json,
        ),
        ProposalArtifact(
            relative_path=f"environments/requests/{request.request_id}.yaml",
            content=_yaml_content(request_document),
        ),
        ProposalArtifact(
            relative_path=(
                f"environments/terraform/{provider.value}/{request.request_id}.json"
            ),
            content=terraform_json,
        ),
        ProposalArtifact(
            relative_path=(
                f"infrastructure/terraform/{provider.value}/"
                f"{request.request_id}.auto.tfvars.json"
            ),
            content=terraform_variables_json,
        ),
    )
    artifacts = tuple(sorted(artifacts, key=lambda artifact: artifact.relative_path))
    artifact_payload = [
        {"content": artifact.content, "path": artifact.relative_path}
        for artifact in artifacts
    ]
    content_hash = hashlib.sha256(
        _stable_json({"identity": identity, "artifacts": artifact_payload}).encode()
    ).hexdigest()
    return DeploymentProposal(
        proposal_id=proposal_id,
        content_hash=content_hash,
        request_id=request.request_id,
        request_fingerprint=request.fingerprint,
        installation_id=profile.installation_id,
        provider=request.provider,
        mode=profile.mode,
        artifacts=artifacts,
    )


__all__ = [
    "DeploymentProposal",
    "BUNDLE_MARKER_FILENAME",
    "PROPOSAL_SCHEMA_VERSION",
    "ProposalArtifact",
    "ProposalBundleMarker",
    "ProposalInputError",
    "ProposalState",
    "build_deployment_proposal",
]
