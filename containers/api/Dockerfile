# RC limitation: exact base tags are pinned; digest promotion is main-review work.
FROM python:3.13.7-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip wheel --wheel-dir /wheels .

FROM python:3.13.7-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --system --gid 10001 platform \
    && useradd --system --uid 10001 --gid 10001 --home-dir /app --create-home platform
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels
USER platform
EXPOSE 8000
CMD ["uvicorn", "secure_cloud_platform.api:app", "--host", "0.0.0.0", "--port", "8000"]
