"""Automation-friendly Typer CLI over the shared application service."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, cast

import typer
import yaml
from pydantic import BaseModel, ValidationError

from .models import (
    EnvironmentRequest,
    InstallationProfile,
    InstallationStatus,
)
from .proposals import (
    BUNDLE_MARKER_FILENAME,
    DeploymentProposal,
    ProposalBundleMarker,
)
from .service import (
    EnvironmentRequestNotFoundError,
    InterfaceError,
    PlatformService,
    ProposalNotFoundError,
)


def _json_default(value: object) -> str:
    return str(value)


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return _jsonable(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _stable_json(value: object) -> str:
    return json.dumps(
        _jsonable(value),
        default=_json_default,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _read_document(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise InterfaceError(f"could not read {path}: {error}") from error
    try:
        if path.suffix.lower() == ".json":
            document = cast(object, json.loads(text))
        else:
            try:
                document = cast(object, yaml.safe_load(text))
            except yaml.YAMLError as error:
                raise InterfaceError(f"could not parse {path}: {error}") from error
    except (ValueError, TypeError) as error:
        raise InterfaceError(f"could not parse {path}: {error}") from error
    if not isinstance(document, dict):
        raise InterfaceError(f"{path} must contain a JSON/YAML object")
    return {str(key): cast(object, value) for key, value in document.items()}


def _profile_from_file(path: Path) -> InstallationProfile:
    document = _read_document(path)
    wrapped = document.get("installation")
    if isinstance(wrapped, dict):
        document = wrapped
    return InstallationProfile.model_validate(document)


def _request_from_file(path: Path) -> EnvironmentRequest:
    return EnvironmentRequest.model_validate(_read_document(path))


def _emit(value: object) -> None:
    typer.echo(_stable_json(value))


def _write_profile(path: Path, profile: InstallationProfile, *, force: bool) -> None:
    if path.exists() and not force:
        raise InterfaceError(
            f"refusing to overwrite existing profile {path}; use --force"
        )
    try:
        path.write_text(_stable_json(profile) + "\n", encoding="utf-8")
    except OSError as error:
        raise InterfaceError(f"could not write profile {path}: {error}") from error


def _service_from_profile(path: Path) -> PlatformService:
    profile = _profile_from_file(path)
    if profile.status is not InstallationStatus.ACTIVE:
        raise InterfaceError("the profile must have active status")
    if profile.provider is None:
        raise InterfaceError("the profile must select a provider")
    service = PlatformService()
    service.create_installation(
        installation_id=profile.installation_id,
        provider=profile.provider,
        mode=profile.mode,
        guardrails=profile.guardrails,
    )
    return service


def _reject_symlink_ancestors(path: Path) -> None:
    """Reject existing symlink components before any bundle replacement."""

    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        if current.is_symlink():
            raise InterfaceError(
                f"refusing to operate through symlinked path component {current}"
            )


def _validate_existing_bundle(
    root: Path,
    marker: ProposalBundleMarker,
) -> None:
    """Require an existing bundle to contain exactly its marked files."""

    files: set[str] = set()
    directories: set[str] = set()
    for current, names, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in names:
            path = current_path / name
            if path.is_symlink():
                raise InterfaceError(
                    "--force may not replace a proposal bundle containing symlinks"
                )
            directories.add(path.relative_to(root).as_posix())
        for filename in filenames:
            path = current_path / filename
            if path.is_symlink():
                raise InterfaceError(
                    "--force may not replace a proposal bundle containing symlinks"
                )
            files.add(path.relative_to(root).as_posix())

    expected_files = {BUNDLE_MARKER_FILENAME, *marker.artifact_paths}
    expected_directories = {
        "/".join(parts[:index])
        for filename in expected_files
        for parts in [filename.split("/")]
        for index in range(1, len(parts))
    }
    if files != expected_files or directories != expected_directories:
        raise InterfaceError(
            "--force may replace only a proposal bundle with exactly its "
            "marked artifacts"
        )


def _materialize_proposal(
    proposal: DeploymentProposal,
    output: Path,
    *,
    force: bool,
) -> None:
    """Atomically materialize a proposal into a new, safe bundle directory."""

    if output.name in {"", ".", ".."}:
        raise InterfaceError("proposal output must have a non-special directory name")
    output_absolute = output.absolute()
    _reject_symlink_ancestors(output_absolute)
    resolved_output = output_absolute.resolve(strict=False)
    if resolved_output in {
        Path.cwd().resolve(),
        Path.home().resolve(),
        Path(resolved_output.anchor),
    }:
        raise InterfaceError(
            "refusing to materialize in the current directory, home, or filesystem root"
        )
    if output_absolute.is_symlink() or output.is_symlink():
        raise InterfaceError("refusing to materialize through a symlinked output")
    output_path = resolved_output
    if output_path.exists() and not output_path.is_dir():
        raise InterfaceError(f"proposal output {output} must be a directory")
    if output_path.exists() and output_path.is_symlink():
        raise InterfaceError("refusing to replace a symlinked proposal output")
    if output_path.exists() and not force:
        raise InterfaceError(
            f"refusing to overwrite proposal output {output}; use --force"
        )
    if output_path.exists():
        marker_path = output_path / BUNDLE_MARKER_FILENAME
        if marker_path.is_symlink() or not marker_path.is_file():
            raise InterfaceError("--force may replace only a marked proposal bundle")
        try:
            marker = ProposalBundleMarker.model_validate(
                json.loads(marker_path.read_text(encoding="utf-8"))
            )
        except (OSError, TypeError, ValueError, ValidationError) as error:
            raise InterfaceError(
                "--force may replace only a proposal bundle with a valid marker"
            ) from error
        if marker.schema_version != proposal.schema_version:
            raise InterfaceError(
                "the existing proposal bundle marker has an unsupported schema"
            )
        _validate_existing_bundle(output_path, marker)

    output_parent = output_path.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_ancestors(output_parent)
    stage: Path | None = Path(
        tempfile.mkdtemp(prefix=f".{output_path.name}-", dir=output_parent)
    )
    backup: Path | None = None
    try:
        assert stage is not None
        root = stage.resolve()
        marker = ProposalBundleMarker(
            proposal_id=proposal.proposal_id,
            content_hash=proposal.content_hash,
            artifact_paths=proposal.artifact_paths,
        )
        (root / BUNDLE_MARKER_FILENAME).write_text(
            _stable_json(marker) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        for artifact in proposal.artifacts:
            target = root / artifact.relative_path
            try:
                target.resolve().relative_to(root)
            except ValueError as error:
                raise InterfaceError(
                    f"proposal artifact path escapes the output directory: "
                    f"{artifact.relative_path}"
                ) from error
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(artifact.content, encoding="utf-8", newline="\n")

        if output_path.exists():
            backup = Path(
                tempfile.mkdtemp(
                    prefix=f".{output_path.name}-backup-",
                    dir=output_parent,
                )
            )
            backup.rmdir()
            os.replace(output_path, backup)
        try:
            os.replace(stage, output_path)
        except OSError:
            if backup is not None and not output_path.exists():
                os.replace(backup, output_path)
                backup = None
            raise
        stage = None
        if backup is not None:
            shutil.rmtree(backup)
            backup = None
    except OSError as error:
        raise InterfaceError(
            f"could not materialize proposal {output}: {error}"
        ) from error
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if backup is not None and backup.exists() and not output_path.exists():
            os.replace(backup, output_path)


def _failure(error: Exception) -> None:
    _emit(
        {
            "error": {
                "code": error.__class__.__name__.removesuffix("Error")
                .replace(" ", "-")
                .lower(),
                "message": str(error),
            }
        }
    )
    raise typer.Exit(code=2)


def create_cli(service: PlatformService | None = None) -> typer.Typer:
    """Create an isolated CLI tree backed by one service instance."""

    platform = PlatformService() if service is None else service
    cli = typer.Typer(
        name="platform",
        no_args_is_help=True,
        help="Self-service cloud platform evaluation and proposal commands.",
    )
    setup = typer.Typer(no_args_is_help=True, help="Installation setup commands.")
    request = typer.Typer(no_args_is_help=True, help="Environment request commands.")
    cli.add_typer(setup, name="setup")
    cli.add_typer(request, name="request")

    @setup.command("init")
    def setup_init(
        provider: Annotated[str, typer.Option(help="aws or azure")],
        mode: Annotated[
            str, typer.Option(help="simulation, sandbox, or enterprise")
        ] = "simulation",
        installation_id: Annotated[
            str, typer.Option(help="Stable installation ID")
        ] = "default",
        output: Annotated[
            Path | None, typer.Option("--output", help="Write the profile JSON here")
        ] = None,
        force: Annotated[
            bool, typer.Option("--force", help="Allow replacing --output")
        ] = False,
    ) -> None:
        try:
            if output is not None and output.exists() and not force:
                raise InterfaceError(
                    f"refusing to overwrite existing profile {output}; use --force"
                )
            profile = platform.create_installation(
                installation_id=installation_id,
                provider=provider,
                mode=mode,
            )
            validation = platform.validate_installation(profile)
            if output is not None:
                _write_profile(output, profile, force=force)
            _emit(
                {
                    "installation": profile,
                    "validation": validation,
                }
            )
            if not validation.allowed:
                raise typer.Exit(code=1)
        except (InterfaceError, ValidationError) as error:
            _failure(error)

    @setup.command("validate")
    def setup_validate(profile: Annotated[Path, typer.Argument()]) -> None:
        try:
            parsed = _profile_from_file(profile)
            validation = PlatformService().validate_installation(parsed)
            _emit(validation)
            if not validation.allowed:
                raise typer.Exit(code=1)
        except (InterfaceError, ValidationError, OSError) as error:
            _failure(error)

    @setup.command("status")
    def setup_status(profile: Annotated[Path, typer.Argument()]) -> None:
        try:
            parsed = _profile_from_file(profile)
            validation = PlatformService().validate_installation(parsed)
            _emit({"installation": parsed, "validation": validation})
            if not validation.allowed:
                raise typer.Exit(code=1)
        except (InterfaceError, ValidationError) as error:
            _failure(error)

    @setup.command("propose")
    def setup_propose(profile: Annotated[Path, typer.Argument()]) -> None:
        """Describe provider bootstrap for operator review; never execute it."""

        try:
            parsed = _profile_from_file(profile)
            if parsed.status is not InstallationStatus.ACTIVE:
                raise InterfaceError("the profile must have active status")
            if parsed.provider is None:
                raise InterfaceError("the profile must select a provider")
            validation = PlatformService().validate_installation(parsed)
            if not validation.allowed:
                raise InterfaceError(
                    "the installation profile does not pass provider validation"
                )
            _emit(
                {
                    "execution": "operator-review-only",
                    "installation_id": parsed.installation_id,
                    "mode": parsed.mode,
                    "provider": parsed.provider,
                    "terraform_root": (
                        f"infrastructure/terraform/{parsed.provider.value}-bootstrap"
                    ),
                }
            )
        except (InterfaceError, ValidationError, OSError) as error:
            _failure(error)

    @request.command("validate")
    def request_validate(
        request_file: Annotated[Path, typer.Argument()],
        profile: Annotated[Path, typer.Option("--profile")],
    ) -> None:
        try:
            parsed = _request_from_file(request_file)
            isolated = _service_from_profile(profile)
            resolved, outcome = isolated.evaluate_environment_request(parsed)
            _emit(
                {
                    "request": resolved,
                    "decision": outcome.decision,
                }
            )
            if not outcome.decision.allowed:
                raise typer.Exit(code=1)
        except (InterfaceError, ValidationError, OSError) as error:
            _failure(error)

    @request.command("render")
    def request_render(
        request_file: Annotated[Path, typer.Argument()],
        profile: Annotated[Path, typer.Option("--profile")],
    ) -> None:
        try:
            parsed = _request_from_file(request_file)
            isolated = _service_from_profile(profile)
            resolved, outcome = isolated.evaluate_environment_request(parsed)
            _emit(
                {
                    "request": resolved,
                    "decision": outcome.decision,
                    "simulation": outcome.result,
                }
            )
            if not outcome.decision.allowed:
                raise typer.Exit(code=1)
        except (InterfaceError, ValidationError, OSError) as error:
            _failure(error)

    @request.command("propose")
    def request_propose(
        request_file: Annotated[Path, typer.Argument()],
        profile: Annotated[Path, typer.Option("--profile")],
        output: Annotated[
            Path | None,
            typer.Option("--output", help="Materialize the proposal bundle here"),
        ] = None,
        force: Annotated[
            bool, typer.Option("--force", help="Allow replacing --output")
        ] = False,
    ) -> None:
        try:
            parsed = _request_from_file(request_file)
            isolated = _service_from_profile(profile)
            resolved, outcome = isolated.evaluate_environment_request(parsed)
            if not outcome.decision.allowed:
                _emit(
                    {
                        "request": resolved,
                        "decision": outcome.decision,
                        "state": "denied",
                    }
                )
                raise typer.Exit(code=1)
            record = isolated.create_environment_request(
                parsed,
                idempotency_key=f"cli-request-{resolved.fingerprint}",
            )
            proposal = isolated.create_deployment_proposal(
                record.request.request_id,
                idempotency_key=f"cli-proposal-{resolved.fingerprint}",
            )
            if output is not None:
                _materialize_proposal(proposal, output, force=force)
            _emit(proposal)
        except (InterfaceError, ValidationError, OSError) as error:
            _failure(error)

    @request.command("status")
    def request_status(
        reference: Annotated[
            str, typer.Argument(help="Request/proposal ID or artifact")
        ],
        profile: Annotated[
            Path | None,
            typer.Option(
                "--profile",
                help="Profile required to evaluate a standalone request artifact",
            ),
        ] = None,
    ) -> None:
        try:
            reference_path = Path(reference)
            if reference_path.is_file():
                document = _read_document(reference_path)
                if "proposal_id" in document:
                    _emit(DeploymentProposal.model_validate(document))
                    return
                if profile is None:
                    raise InterfaceError(
                        "a request artifact requires --profile for "
                        "process-independent status"
                    )
                parsed = EnvironmentRequest.model_validate(document)
                isolated = _service_from_profile(profile)
                resolved, outcome = isolated.evaluate_environment_request(parsed)
                _emit(
                    {
                        "request": resolved,
                        "decision": outcome.decision,
                        "state": "accepted" if outcome.decision.allowed else "denied",
                    }
                )
                return

            try:
                _emit(platform.get_deployment_proposal(reference))
                return
            except ProposalNotFoundError:
                try:
                    _emit(platform.get_environment_request(reference))
                    return
                except EnvironmentRequestNotFoundError as error:
                    raise InterfaceError(
                        "request and proposal IDs are process-local; provide an "
                        "artifact file or use the same service process"
                    ) from error
        except (InterfaceError, ValidationError, OSError) as error:
            _failure(error)

    return cli


app = create_cli()


if __name__ == "__main__":
    app()


__all__ = ["app", "create_cli"]
