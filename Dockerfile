FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b
WORKDIR /app
ARG QJAI_PROJECT_NAME=qjai-agent-template
LABEL org.opencontainers.image.title=${QJAI_PROJECT_NAME}
ENV AGENT_NAME=${QJAI_PROJECT_NAME}
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY qjai_agent/ ./qjai_agent/
CMD ["python", "-m", "qjai_agent"]
