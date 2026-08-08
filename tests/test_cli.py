import json

from typer.testing import CliRunner

from secure_cloud_platform.cli import create_cli
from secure_cloud_platform.service import PlatformService
from test_service import make_request


def test_cli_profile_file_supports_separate_aws_processes(tmp_path) -> None:
    profile = tmp_path / "aws-profile.json"
    request_file = tmp_path / "request.json"
    request_file.write_text(
        json.dumps(make_request().model_dump(mode="json")), encoding="utf-8"
    )
    runner = CliRunner()
    setup = runner.invoke(
        create_cli(),
        ["setup", "init", "--provider", "aws", "--output", str(profile)],
    )
    assert setup.exit_code == 0, setup.stdout
    assert profile.exists()
    assert json.loads(profile.read_text(encoding="utf-8"))["provider"] == "aws"

    validation = runner.invoke(create_cli(), ["setup", "validate", str(profile)])
    assert validation.exit_code == 0, validation.stdout
    status = runner.invoke(create_cli(), ["setup", "status", str(profile)])
    assert status.exit_code == 0, status.stdout

    result = runner.invoke(
        create_cli(),
        ["request", "validate", str(request_file), "--profile", str(profile)],
    )
    assert result.exit_code == 0, result.stdout
    output = json.loads(result.stdout)
    direct_service = PlatformService()
    direct_service.create_installation(provider="aws")
    resolved, outcome = direct_service.evaluate_environment_request(make_request())
    assert output["request"]["request_id"] == resolved.request_id
    assert output["decision"] == outcome.decision.model_dump(mode="json")


def test_cli_profile_file_supports_azure_and_render(tmp_path) -> None:
    profile = tmp_path / "azure-profile.json"
    request_file = tmp_path / "request.json"
    request_file.write_text(
        json.dumps(make_request(region="northeurope").model_dump(mode="json")),
        encoding="utf-8",
    )
    runner = CliRunner()
    setup = runner.invoke(
        create_cli(),
        ["setup", "init", "--provider", "azure", "--output", str(profile)],
    )
    assert setup.exit_code == 0, setup.stdout
    render = runner.invoke(
        create_cli(),
        ["request", "render", str(request_file), "--profile", str(profile)],
    )
    assert render.exit_code == 0, render.stdout
    output = json.loads(render.stdout)
    assert output["request"]["provider"] == "azure"
    assert output["simulation"]["provider"] == "azure"


def test_cli_refuses_profile_overwrite_without_force(tmp_path) -> None:
    profile = tmp_path / "profile.json"
    profile.write_text("existing\n", encoding="utf-8")
    result = CliRunner().invoke(
        create_cli(),
        ["setup", "init", "--provider", "aws", "--output", str(profile)],
    )
    assert result.exit_code == 2
    assert "force" in result.stdout


def test_cli_has_no_apply_plan_or_destroy_command() -> None:
    result = CliRunner().invoke(create_cli(), ["--help"])
    assert "apply" not in result.stdout
    assert "plan" not in result.stdout
    assert "destroy" not in result.stdout
