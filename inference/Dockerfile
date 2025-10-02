FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy ONLY inference code into /app
COPY inference/ .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8082"]