FROM python:3.12-alpine3.20

# set working dir
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# install build deps (if any)
RUN apk add --no-cache build-base libpq

# copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy app source into the image
# ensure the "app" package directory from services/orchestrator is placed under /app
COPY services/orchestrator/ /app/

# expose port used by orchestrator
EXPOSE 8000

# run uvicorn. (No --reload for stable container; add --reload only if you want reloader)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
