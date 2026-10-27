ARG BUILD_FROM=python:3.14-slim

# Build stage: fetch the evcc optimizer from GitHub and install its dependencies
FROM $BUILD_FROM AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# the runtime stage copies only the venv: fail here if the image python does not
# satisfy the optimizer's, instead of linking the venv to a python uv downloaded
ENV UV_PYTHON_DOWNLOADS=never

# Fetch the pinned optimizer commit from GitHub
ARG EVOPT_REPO=https://github.com/evcc-io/optimizer.git
ARG EVOPT_COMMIT=main
WORKDIR /app
RUN git init -q . \
    && git remote add origin "$EVOPT_REPO" \
    && git fetch -q --depth 1 origin "$EVOPT_COMMIT" \
    && git checkout -q FETCH_HEAD

RUN uv sync --locked --no-editable --no-group dev

# PuLP 4 resolves CBC from PATH instead of bundling it. Use upstream's
# checksum-verified CBC 2.10.10 build on amd64 and Debian's CBC on arm64.
RUN mkdir -p /out/bin \
    && if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
        curl -fsSL -o /tmp/cbc.tar.gz "https://github.com/coin-or/Cbc/releases/download/releases%2F2.10.10/Cbc-releases.2.10.10-x86_64-ubuntu22-gcc1130-static.tar.gz" \
        && echo "f551e7b843e25becee466a447118f6f44f219c4e46cfb4670829ecd3cf47e7d8  /tmp/cbc.tar.gz" | sha256sum -c - \
        && tar -xzf /tmp/cbc.tar.gz -C /out ./bin/cbc; \
    fi

FROM $BUILD_FROM

# Create non-root user
RUN groupadd -r app && useradd -r -g app -s /bin/false app

# Copy the environment, but not the source code
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder /out/ /usr/local/

RUN if [ "$(dpkg --print-architecture)" != "amd64" ]; then \
        apt-get update \
        && apt-get install -y --no-install-recommends coinor-cbc \
        && rm -rf /var/lib/apt/lists/*; \
    fi \
    && echo | "$(/app/.venv/bin/python -c 'import pulp; print(pulp.COIN_CMD().path)')" \
        | grep -q 'Version: 2.10'

# Run the application
ENV PYTHONUNBUFFERED=1
ENV OPTIMIZER_TIME_LIMIT=10
ENV OPTIMIZER_NUM_THREADS=1
ENV OPTIMIZER_SOLVER=highs
# the access log is the only source of per request latency, keep the format lean.
# the config module reaps solvers left behind by a killed worker, see gunicorn_conf.py
ENV GUNICORN_CMD_ARGS="--workers 4 --max-requests 32 --config python:optimizer.gunicorn_conf --access-logfile - --access-logformat '%(m)s %(U)s %(s)s %(D)s'"
USER app
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:7050", "optimizer.app:app"]
