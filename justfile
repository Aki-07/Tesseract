# Set shell
set shell := ["bash", "-cu"]

# Start everything
up:
    docker compose up --build -d

# Stop everything + remove volumes
down:
    docker compose down -v

# Show running services
ps:
    docker compose ps

# Tail logs
logs:
    docker compose logs -f --tail=100

# Restart everything fresh
restart:
    docker compose down -v
    docker compose up --build -d

# Run orchestrator locally (bypassing Docker)
orchestrator-local:
    uvicorn orchestrator.main:app --reload --port 8081

# Run inference locally (bypassing Docker)
inference-local:
    uvicorn inference.server:app --reload --port 8082
