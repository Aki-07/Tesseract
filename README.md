# 🧠 Tessera: The Neural Battlefield

Tessera is an AI-vs-AI simulation platform where autonomous **attackers** and **defenders**—powered by large language models (LLMs)—battle in real time.  
Each round is orchestrated by a central intelligence layer that evaluates performance, detects breaches, and evolves the agents over time.

---

## ⚙️ Architecture Overview

- **Frontend** — Built in Next.js + TailwindCSS  
  Interactive dashboard to visualize battles, run histories, and performance metrics.

- **Orchestrator (FastAPI)** — Core battle engine  
  Coordinates multi-round simulations between AI models, tracks results, and logs all metrics.

- **Docker MCP Capsules** — Dynamic model containers  
  Each attacker/defender runs as an isolated **capsule**, a Docker container that hosts an AI model instance (Llama, Falcon, Cerebras, etc.).  
  Capsules can be spawned, listed, or stopped dynamically through the Orchestrator API.

- **Cerebras Integration** — Judgment Engine  
  Cerebras inference API acts as the **referee**, evaluating responses and identifying semantic breaches or weaknesses between attacker and defender models.

- **Database (SQLite)** — Tracks simulation runs and capsule metadata.

---

## 🧩 Sponsor Technology Highlights

### 🐳 Docker MCP Gateway
We used Docker’s **Model Context Protocol (MCP)** to dynamically spawn, register, and manage model “capsules.”  
This enables:
- Isolated execution of each model in its own container.
- Real-time orchestration via REST endpoints.
- Scalable model swapping and benchmarking without code changes.

### 🦙 Llama
Llama models power both **attackers** and **defenders**, each with a specific prompt strategy.  
They generate text responses that simulate adversarial and defensive reasoning.

### ⚡ Cerebras
Cerebras inference API is used as an independent **judge** that scores each round—detecting breaches and summarizing attack outcomes.

---


## 📊 Observability Layer

### 🧠 Prometheus
The Orchestrator exposes internal metrics (battle rounds, breach counts, latency) at  
**`/metrics`** endpoint, automatically scraped by Prometheus.

**Example configuration (`config/prometheus/prometheus.yml`):**
```yaml
scrape_configs:
  - job_name: 'tessera'
    static_configs:
      - targets: ['orchestrator:8080']

## 🎮 Features

- 🔁 Real-time attacker vs defender battles  
- 📊 Live breach rate charts  
- 🧩 Capsule registry for managing model deployments  
- 🧠 Intelligent orchestration with Cerebras scoring  
- 💾 Persistent run history and replay support  

---

## 🚀 How to Run Locally

```bash
# 1. Start core services
docker compose -f docker-compose.yaml up --build

# 2. Start frontend (Next.js)
cd services/tessera-ui
npm run dev
