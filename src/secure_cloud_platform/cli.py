"""Automation-friendly Typer CLI over the shared application service."""

from __future__ import annotations

import json
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
from .service import InterfaceError, PlatformService


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
        help="Self-service cloud platform simulation commands.",
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

    return cli


app = create_cli()


if __name__ == "__main__":
    app()


__all__ = ["app", "create_cli"]
