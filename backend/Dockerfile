FROM python:3.12-slim

ENV PYTHONHASHSEED=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY src ./src
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "resumematch.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
