import hashlib
import ipaddress
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from secure_cloud_platform.api import create_app
from secure_cloud_platform.cli import _materialize_proposal, create_cli
from secure_cloud_platform.proposals import DeploymentProposal, ProposalArtifact
from secure_cloud_platform.service import (
    IdempotencyConflictError,
    IdempotencyKeyRequiredError,
    InterfaceError,
    PlatformService,
    ProposalNotAllowedError,
)
from test_service import make_request


@pytest.mark.parametrize(
    ("provider", "region", "mode"),
    [
        ("aws", "eu-west-1", "simulation"),
        ("aws", "eu-west-1", "sandbox"),
        ("aws", "eu-west-1", "enterprise"),
        ("azure", "northeurope", "simulation"),
        ("azure", "northeurope", "sandbox"),
        ("azure", "northeurope", "enterprise"),
    ],
)
def test_proposal_is_deterministic_and_has_safe_textual_artifacts(
    provider: str, region: str, mode: str
) -> None:
    first_service = PlatformService()
    second_service = PlatformService()
    first_service.create_installation(provider=provider, mode=mode)
    second_service.create_installation(provider=provider, mode=mode)
    request = make_request(region=region)

    first_record = first_service.create_environment_request(
        request, idempotency_key=f"request-{provider}"
    )
    second_record = second_service.create_environment_request(
        request, idempotency_key=f"request-{provider}"
    )
    first = first_service.create_deployment_proposal(
        first_record.request.request_id, idempotency_key=f"proposal-{provider}"
    )
    second = second_service.create_deployment_proposal(
        second_record.request.request_id, idempotency_key=f"proposal-{provider}"
    )

    assert first == second
    assert first.proposal_id.startswith("proposal-")
    assert first.content_hash
    assert len(first.artifacts) == 7
    assert all(
        not Path(artifact.relative_path).is_absolute() for artifact in first.artifacts
    )
    assert all(
        ".." not in Path(artifact.relative_path).parts for artifact in first.artifacts
    )
    assert {Path(artifact.relative_path).suffix for artifact in first.artifacts} >= {
        ".json",
        ".yaml",
        ".md",
    }
    assert any("terraform" in artifact.relative_path for artifact in first.artifacts)
    identity_artifact = next(
        artifact
        for artifact in first.artifacts
        if artifact.relative_path == f"environments/proposals/{first.proposal_id}.json"
    )
    expected_identity = {
        "installation_id": "default",
        "mode": mode,
        "proposal_id": first.proposal_id,
        "provider": provider,
        "request_fingerprint": first.request_fingerprint,
        "request_id": first.request_id,
        "schema_version": "proposal.v1",
        "state": "ready_for_review",
    }
    assert json.loads(identity_artifact.content) == expected_identity
    assert identity_artifact.content == json.dumps(
        expected_identity,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    assert all(
        forbidden not in expected_identity
        for forbidden in (
            "account_id",
            "client_secret",
            "content_hash",
            "email",
            "oidc",
            "password",
            "subscription_id",
            "tenant_id",
            "token",
        )
    )
    hash_identity = {
        "installation_id": "default",
        "mode": mode,
        "provider": provider,
        "proposal_schema_version": "proposal.v1",
        "request": json.loads(first_record.request.canonical_json),
    }
    artifact_payload = [
        {"content": artifact.content, "path": artifact.relative_path}
        for artifact in first.artifacts
    ]
    expected_hash_payload = json.dumps(
        {"artifacts": artifact_payload, "identity": hash_identity},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert (
        first.content_hash
        == hashlib.sha256(expected_hash_payload.encode("utf-8")).hexdigest()
    )
    tfvars_artifact = next(
        artifact
        for artifact in first.artifacts
        if artifact.relative_path.endswith(".auto.tfvars.json")
    )
    tfvars = json.loads(tfvars_artifact.content)
    if provider == "aws":
        assert set(tfvars) == {
            "desired_nodes",
            "mode",
            "monthly_budget_usd",
            "name_prefix",
            "private_subnet_cidrs",
            "public_subnet_cidrs",
            "region",
            "vpc_cidr",
        }
        root = ipaddress.ip_network(tfvars["vpc_cidr"])
        private = [
            ipaddress.ip_network(cidr) for cidr in tfvars["private_subnet_cidrs"]
        ]
        public = [ipaddress.ip_network(cidr) for cidr in tfvars["public_subnet_cidrs"]]
        assert all(subnet.subnet_of(root) for subnet in private + public)
        assert len(set(private + public)) == len(private) + len(public)
        assert re.fullmatch(r"[a-z0-9-]+", tfvars["name_prefix"])
        assert "account" not in tfvars and "oidc" not in tfvars
        assert tfvars_artifact.relative_path.startswith("infrastructure/terraform/aws/")
    else:
        assert set(tfvars) == {
            "desired_nodes",
            "location",
            "mode",
            "monthly_budget_eur",
            "name_prefix",
            "private_subnet_prefixes",
            "vnet_address_space",
        }
        root = ipaddress.ip_network(tfvars["vnet_address_space"][0])
        private = [
            ipaddress.ip_network(cidr) for cidr in tfvars["private_subnet_prefixes"]
        ]
        assert all(subnet.subnet_of(root) for subnet in private)
        assert len(set(private)) == len(private)
        assert "tenant_id" not in tfvars and "subscription_id" not in tfvars
        assert tfvars_artifact.relative_path.startswith(
            "infrastructure/terraform/azure/"
        )


def test_denied_request_cannot_produce_proposal() -> None:
    service = PlatformService()
    service.create_installation(provider="aws")
    record = service.create_environment_request(
        make_request(network_cidr="8.8.8.0/24"), idempotency_key="denied"
    )
    assert record.state == "denied"
    with pytest.raises(ProposalNotAllowedError):
        service.create_deployment_proposal(
            record.request.request_id, idempotency_key="proposal"
        )


def test_insufficient_cidr_fails_as_typed_proposal_not_allowed() -> None:
    service = PlatformService()
    service.create_installation(provider="aws")
    record = service.create_environment_request(
        make_request(network_cidr="10.0.0.0/30"), idempotency_key="small-cidr"
    )
    assert record.state == "accepted"
    with pytest.raises(ProposalNotAllowedError, match="required.*subnets"):
        service.create_deployment_proposal(
            record.request.request_id, idempotency_key="small-cidr-proposal"
        )


def test_proposal_idempotency_conflict_and_concurrency() -> None:
    service = PlatformService()
    service.create_installation(provider="aws")
    record = service.create_environment_request(
        make_request(), idempotency_key="request"
    )

    def submit(index: int):
        return service.create_deployment_proposal(
            record.request.request_id, idempotency_key=f"proposal-{index}"
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        proposals = list(executor.map(submit, range(8)))
    assert all(proposal == proposals[0] for proposal in proposals)
    assert len(service.list_deployment_proposals()) == 1
    other_record = service.create_environment_request(
        make_request(application="other-api"), idempotency_key="other-request"
    )
    with pytest.raises(IdempotencyConflictError):
        service.create_deployment_proposal(
            other_record.request.request_id, idempotency_key="proposal-0"
        )
    with pytest.raises(IdempotencyKeyRequiredError):
        service.create_deployment_proposal(
            record.request.request_id, idempotency_key=" "
        )


@pytest.mark.parametrize("mode", ["simulation", "sandbox", "enterprise"])
def test_api_and_cli_proposals_are_equivalent_and_api_has_no_apply_path(
    tmp_path: Path, mode: str
) -> None:
    profile = tmp_path / "profile.json"
    request_file = tmp_path / "request.json"
    proposal_file = tmp_path / "proposal.json"
    request_file.write_text(
        json.dumps(make_request().model_dump(mode="json")), encoding="utf-8"
    )
    runner = CliRunner()
    assert (
        runner.invoke(
            create_cli(),
            [
                "setup",
                "init",
                "--provider",
                "aws",
                "--mode",
                mode,
                "--output",
                str(profile),
            ],
        ).exit_code
        == 0
    )
    cli_result = runner.invoke(
        create_cli(),
        ["request", "propose", str(request_file), "--profile", str(profile)],
    )
    assert cli_result.exit_code == 0, cli_result.stdout
    cli_proposal = json.loads(cli_result.stdout)
    proposal_file.write_text(cli_result.stdout, encoding="utf-8")

    service = PlatformService()
    client = TestClient(create_app(service))
    assert (
        client.post(
            "/v1/platform/installations",
            json={"provider": "aws", "mode": mode},
        ).status_code
        == 201
    )
    request_response = client.post(
        "/v1/environment-requests",
        json=make_request().model_dump(mode="json"),
        headers={"Idempotency-Key": "api-request"},
    )
    proposal_response = client.post(
        "/v1/deployment-proposals",
        json={"request_id": request_response.json()["request"]["request_id"]},
        headers={"Idempotency-Key": "api-proposal"},
    )
    assert proposal_response.status_code == 201
    assert cli_proposal == proposal_response.json()
    assert DeploymentProposal.model_validate(json.loads(proposal_file.read_text()))
    paths = {route.path for route in create_app().routes}
    assert not any(
        action in path for path in paths for action in ("apply", "plan", "destroy")
    )


def test_cli_materialization_is_safe_and_force_is_explicit(tmp_path: Path) -> None:
    profile = tmp_path / "profile.json"
    request_file = tmp_path / "request.json"
    bundle = tmp_path / "bundle"
    request_file.write_text(
        json.dumps(make_request().model_dump(mode="json")), encoding="utf-8"
    )
    runner = CliRunner()
    assert (
        runner.invoke(
            create_cli(),
            ["setup", "init", "--provider", "aws", "--output", str(profile)],
        ).exit_code
        == 0
    )
    command = [
        "request",
        "propose",
        str(request_file),
        "--profile",
        str(profile),
        "--output",
        str(bundle),
    ]
    first = runner.invoke(create_cli(), command)
    assert first.exit_code == 0, first.stdout
    proposal = DeploymentProposal.model_validate(json.loads(first.stdout))
    assert all(
        (bundle / artifact.relative_path).is_file() for artifact in proposal.artifacts
    )
    second = runner.invoke(create_cli(), command)
    assert second.exit_code == 2
    assert "force" in second.stdout
    third = runner.invoke(create_cli(), [*command, "--force"])
    assert third.exit_code == 0, third.stdout
    assert all(
        (bundle / artifact.relative_path).read_text() == artifact.content
        for artifact in proposal.artifacts
    )


def test_proposal_artifact_rejects_path_escape() -> None:
    with pytest.raises(ValueError):
        ProposalArtifact(relative_path="../outside.txt", content="unsafe")


def test_materialization_fail_closed_for_special_and_unmarked_paths(
    tmp_path: Path,
) -> None:
    service = PlatformService()
    service.create_installation(provider="aws")
    record = service.create_environment_request(
        make_request(), idempotency_key="materialize-request"
    )
    proposal = service.create_deployment_proposal(
        record.request.request_id, idempotency_key="materialize-proposal"
    )

    with pytest.raises(InterfaceError):
        _materialize_proposal(proposal, Path("."), force=True)

    ordinary = tmp_path / "ordinary"
    ordinary.mkdir()
    sentinel = ordinary / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    with pytest.raises(InterfaceError):
        _materialize_proposal(proposal, ordinary, force=True)
    assert sentinel.read_text(encoding="utf-8") == "keep"

    symlink_target = tmp_path / "symlink-target"
    symlink_target.mkdir()
    symlink = tmp_path / "symlink"
    symlink.symlink_to(symlink_target, target_is_directory=True)
    with pytest.raises(InterfaceError):
        _materialize_proposal(proposal, symlink, force=True)
    assert symlink.is_symlink()
    assert not (symlink_target / ".platform-proposal.json").exists()

    malformed = tmp_path / "malformed"
    malformed.mkdir()
    marker = malformed / ".platform-proposal.json"
    marker.write_text('{"not":"a marker"}\n', encoding="utf-8")
    with pytest.raises(InterfaceError):
        _materialize_proposal(proposal, malformed, force=True)
    assert marker.read_text(encoding="utf-8") == '{"not":"a marker"}\n'


def test_materialization_force_accepts_only_a_valid_marked_bundle(
    tmp_path: Path,
) -> None:
    service = PlatformService()
    service.create_installation(provider="aws")
    record = service.create_environment_request(
        make_request(), idempotency_key="marked-request"
    )
    proposal = service.create_deployment_proposal(
        record.request.request_id, idempotency_key="marked-proposal"
    )
    bundle = tmp_path / "marked-bundle"
    _materialize_proposal(proposal, bundle, force=False)
    marker = json.loads(
        (bundle / ".platform-proposal.json").read_text(encoding="utf-8")
    )
    assert marker["proposal_id"] == proposal.proposal_id
    assert marker["content_hash"] == proposal.content_hash
    assert marker["artifact_paths"] == list(proposal.artifact_paths)
    assert (
        f"environments/proposals/{proposal.proposal_id}.json"
        in marker["artifact_paths"]
    )
    _materialize_proposal(proposal, bundle, force=True)
    assert (bundle / ".platform-proposal.json").is_file()


def test_valid_looking_marker_with_unrelated_data_is_not_replaceable(
    tmp_path: Path,
) -> None:
    service = PlatformService()
    service.create_installation(provider="aws")
    record = service.create_environment_request(
        make_request(), idempotency_key="unrelated-request"
    )
    proposal = service.create_deployment_proposal(
        record.request.request_id, idempotency_key="unrelated-proposal"
    )
    bundle = tmp_path / "unrelated-bundle"
    bundle.mkdir()
    (bundle / ".platform-proposal.json").write_text(
        json.dumps(
            {
                "artifact_paths": list(proposal.artifact_paths),
                "content_hash": proposal.content_hash,
                "proposal_id": proposal.proposal_id,
                "schema_version": proposal.schema_version,
            }
        ),
        encoding="utf-8",
    )
    unrelated = bundle / "unrelated.txt"
    unrelated.write_text("must remain", encoding="utf-8")
    with pytest.raises(InterfaceError):
        _materialize_proposal(proposal, bundle, force=True)
    assert unrelated.read_text(encoding="utf-8") == "must remain"


@pytest.mark.parametrize(
    ("provider", "root"),
    [
        ("aws", "infrastructure/terraform/aws-bootstrap"),
        ("azure", "infrastructure/terraform/azure-bootstrap"),
    ],
)
def test_setup_propose_is_deterministic_review_only(
    tmp_path: Path, provider: str, root: str
) -> None:
    profile = tmp_path / f"{provider}-profile.json"
    runner = CliRunner()
    setup = runner.invoke(
        create_cli(),
        ["setup", "init", "--provider", provider, "--output", str(profile)],
    )
    assert setup.exit_code == 0, setup.stdout
    first = runner.invoke(create_cli(), ["setup", "propose", str(profile)])
    second = runner.invoke(create_cli(), ["setup", "propose", str(profile)])
    assert first.exit_code == 0, first.stdout
    assert first.stdout == second.stdout
    assert json.loads(first.stdout) == {
        "execution": "operator-review-only",
        "installation_id": "default",
        "mode": "simulation",
        "provider": provider,
        "terraform_root": root,
    }
