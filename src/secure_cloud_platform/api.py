"""FastAPI interface over :class:`PlatformService`.

This module contains transport schemas and error mapping only.  All platform
behavior remains in the shared service so API and CLI decisions stay equal.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette import status

from .errors import DomainError
from .models import (
    CloudProvider,
    EnvironmentRequest,
    InstallationGuardrails,
    InstallationMode,
    InstallationProfile,
)
from .service import (
    APPLICATION_VERSION,
    EnvironmentRequestNotFoundError,
    EnvironmentRequestRecord,
    IdempotencyConflictError,
    IdempotencyKeyRequiredError,
    InstallationAlreadyExistsError,
    InstallationNotFoundError,
    InstallationRejectedError,
    InstallationValidation,
    InterfaceError,
    InvalidInterfaceInputError,
    ModeDescriptor,
    PlatformService,
    ProviderDescriptor,
    UnsupportedSimulationError,
)


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class InstallationCreateBody(APIModel):
    installation_id: str = Field(default="default", min_length=1)
    provider: CloudProvider
    mode: InstallationMode = InstallationMode.SIMULATION
    guardrails: InstallationGuardrails | None = None


class InstallationResponse(APIModel):
    installation: InstallationProfile
    validation: InstallationValidation | None = None


class ProviderListResponse(APIModel):
    providers: tuple[ProviderDescriptor, ...]


class ModeListResponse(APIModel):
    modes: tuple[ModeDescriptor, ...]


class RequestListResponse(APIModel):
    requests: tuple[EnvironmentRequestRecord, ...]


class ErrorResponse(APIModel):
    code: str
    message: str
    fields: tuple[dict[str, str], ...] = ()


class ErrorEnvelope(APIModel):
    error: ErrorResponse


def _error_response(
    code: str,
    message: str,
    *,
    status_code: int,
    fields: tuple[dict[str, str], ...] = (),
) -> JSONResponse:
    body = ErrorEnvelope(error=ErrorResponse(code=code, message=message, fields=fields))
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body),
    )


def _service_error_status(error: InterfaceError) -> int:
    if isinstance(error, InstallationRejectedError):
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    if isinstance(
        error,
        (InstallationNotFoundError, EnvironmentRequestNotFoundError),
    ):
        return status.HTTP_404_NOT_FOUND
    if isinstance(
        error,
        (
            IdempotencyConflictError,
            InstallationAlreadyExistsError,
            UnsupportedSimulationError,
        ),
    ):
        return status.HTTP_409_CONFLICT
    if isinstance(error, InvalidInterfaceInputError):
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    if isinstance(error, IdempotencyKeyRequiredError):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_503_SERVICE_UNAVAILABLE if "unavailable" in str(error) else 400


def _interface_error_code(error: InterfaceError) -> str:
    if isinstance(error, IdempotencyConflictError):
        return "idempotency-conflict"
    if isinstance(error, IdempotencyKeyRequiredError):
        return "idempotency-key-required"
    if isinstance(error, InstallationAlreadyExistsError):
        return "installation-already-exists"
    if isinstance(error, InstallationNotFoundError):
        return "installation-not-found"
    if isinstance(error, InstallationRejectedError):
        return "installation-rejected"
    if isinstance(error, InvalidInterfaceInputError):
        return "validation-error"
    if isinstance(error, EnvironmentRequestNotFoundError):
        return "request-not-found"
    if isinstance(error, UnsupportedSimulationError):
        return "simulation-only"
    return "interface-error"


def create_app(service: PlatformService | None = None) -> FastAPI:
    """Create an isolated API application and its process-local service."""

    platform = PlatformService() if service is None else service
    app = FastAPI(
        title="Secure Self-Service Cloud Platform",
        version=APPLICATION_VERSION,
        description=(
            "Credential-free simulation interfaces for a provider-locked "
            "self-service cloud platform."
        ),
    )

    @app.exception_handler(InterfaceError)
    async def interface_error_handler(
        request: Request, error: InterfaceError
    ) -> JSONResponse:
        del request
        code = _interface_error_code(error)
        fields: tuple[dict[str, str], ...] = ()
        if isinstance(error, InstallationRejectedError):
            fields = tuple(
                {
                    "code": violation.code,
                    "field": violation.field,
                    "message": violation.message,
                }
                for violation in error.validation.violations
            )
        return _error_response(
            code,
            str(error),
            status_code=_service_error_status(error),
            fields=fields,
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request, error: DomainError
    ) -> JSONResponse:
        del request
        return _error_response("domain-error", str(error), status_code=400)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request, error: Exception
    ) -> JSONResponse:
        del request, error
        return _error_response(
            "interface-error",
            "The interface could not complete the operation.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        del request
        fields = tuple(
            {
                "field": ".".join(str(part) for part in item["loc"]),
                "message": str(item["msg"]),
            }
            for item in error.errors()
        )
        return _error_response(
            "validation-error",
            "The request contains invalid fields.",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            fields=fields,
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "simulation": True}

    @app.get("/version")
    def app_version() -> dict[str, str]:
        return {
            "name": "secure-self-service-cloud-platform",
            "version": APPLICATION_VERSION,
        }

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        return platform.metrics()

    @app.post(
        "/v1/platform/installations",
        response_model=InstallationResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_installation(body: InstallationCreateBody) -> InstallationResponse:
        profile = platform.create_installation(
            installation_id=body.installation_id,
            provider=body.provider,
            mode=body.mode,
            guardrails=body.guardrails,
        )
        return InstallationResponse(
            installation=profile,
            validation=platform.validate_installation(profile),
        )

    @app.get("/v1/platform/installation", response_model=InstallationProfile)
    def get_installation() -> InstallationProfile:
        return platform.get_installation()

    @app.post(
        "/v1/platform/installation/validate",
        response_model=InstallationValidation,
    )
    def validate_installation() -> InstallationValidation:
        return platform.validate_installation()

    @app.get("/v1/platform/providers", response_model=ProviderListResponse)
    def providers() -> ProviderListResponse:
        return ProviderListResponse(providers=platform.providers())

    @app.get("/v1/platform/modes", response_model=ModeListResponse)
    def modes() -> ModeListResponse:
        return ModeListResponse(modes=platform.modes())

    @app.post(
        "/v1/environment-requests",
        response_model=EnvironmentRequestRecord,
    )
    def create_environment_request(
        request_body: EnvironmentRequest,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> JSONResponse | EnvironmentRequestRecord:
        if idempotency_key is None or not idempotency_key.strip():
            raise IdempotencyKeyRequiredError("an Idempotency-Key header is required")
        record = platform.create_environment_request(
            request_body, idempotency_key=idempotency_key
        )
        return record

    @app.get("/v1/environment-requests", response_model=RequestListResponse)
    def list_environment_requests() -> RequestListResponse:
        return RequestListResponse(requests=platform.list_environment_requests())

    @app.get(
        "/v1/environment-requests/{request_id}",
        response_model=EnvironmentRequestRecord,
    )
    def get_environment_request(request_id: str) -> EnvironmentRequestRecord:
        return platform.get_environment_request(request_id)

    return app


app = create_app()

__all__ = ["app", "create_app"]
