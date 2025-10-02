# Tesseract project commands

set shell := ["bash", "-cu"]

# Install dependencies for orchestrator
install:
    pip install -r services/orchestrator/requirements.txt

# Run orchestrator locally with uvicorn
run:
    uvicorn services.orchestrator.app.main:app --reload --host ${HOST:-0.0.0.0} --port ${PORT:-8000}

# Bring up docker compose
up:
    docker compose up --build

# Shut down docker compose
down:
    docker compose down -v

# Tail logs
logs:
    docker compose logs -f --tail=200

# Format code (using ruff)
fmt:
    ruff format

# Lint code (using ruff)
lint:
    ruff check
