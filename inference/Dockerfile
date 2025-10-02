FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inference/server.py .

EXPOSE 8082

CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8082","--log-level","info"]
