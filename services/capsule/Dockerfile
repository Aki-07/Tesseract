FROM python:3.12-alpine3.20
WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/capsule ./services/capsule

ENV ADAPTER_ID=defender-demo ADAPTER_PATH=/data/adapter
VOLUME ["/data/adapter"]

EXPOSE 9000
CMD ["uvicorn", "services.capsule.mcp_server:app", "--host", "0.0.0.0", "--port", "9000"]