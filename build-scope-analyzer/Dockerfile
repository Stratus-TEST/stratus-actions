FROM alpine:latest AS build

WORKDIR /app

RUN apk --no-cache upgrade && apk --no-cache add gcc musl-dev python3 py3-pip

COPY pyproject.toml /app/
RUN python3 -m venv /venv
RUN /venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir .

FROM alpine:latest

RUN apk --no-cache add git python3 py3-pip

LABEL org.opencontainers.image.source="https://github.com/stratus-test/stratus-actions"
LABEL org.opencontainers.image.description="Build Scope Analyzer - Analyze git changes to identify what needs to be built"
LABEL org.opencontainers.image.licenses=MIT

COPY --from=build /venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/venv/lib/python3.14/site-packages"

WORKDIR /github/workspace
COPY main.py /app/

# RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
#     chown -R appuser:appgroup /app
# USER appuser

RUN git config --global --add safe.directory /github/workspace

ENTRYPOINT ["python3", "-u", "/app/main.py"]

CMD ["--help"]