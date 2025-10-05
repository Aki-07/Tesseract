# syntax=docker/dockerfile:1

FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY services/orchestrator/ /app/

# Create data folder
RUN mkdir -p /data

# Expose orchestrator API
EXPOSE 8000

ENV DATA_DIR=/data
ENV DB_URL=sqlite:///data/capsule_registry.db
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
