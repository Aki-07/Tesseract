FROM python:3.12-alpine3.20

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# install build deps if needed
RUN apk add --no-cache build-base

# install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy capsule source into image (this will include mcp_server.py etc)
COPY services/capsule/ /app/

# expose capsule port (9000)
EXPOSE 9000

# run uvicorn for capsule
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "9000"]
