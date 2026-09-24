# Docker Containerization Guide — MPLADS Intelligence Platform

This directory contains container definitions and orchestration scripts to run the complete MPLADS Autonomous Intelligence & Oversight Platform in an isolated, production-grade Docker environment.

---

## 🏗️ Architecture

```
                          ┌───────────────────────────┐
                          │    Browser Client (3000)   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   Nginx Reverse Proxy     │
                          │   (Frontend Container)    │
                          │   Port 80 (Host: 3000)    │
                          └───────┬───────────┬───────┘
                                  │           │
                    Static SPA    │           │ Reverse Proxy
                    (/, /index)   │           │ (/api/*)
                                  ▼           ▼
                         React 18 SPA     ┌───────────────────────────┐
                                          │   FastAPI Python Backend  │
                                          │   (Backend Container)     │
                                          │   Port 8000               │
                                          └─────────────┬─────────────┘
                                                        │
                                                        ▼
                                          ┌───────────────────────────┐
                                          │   Named Docker Volume     │
                                          │   (audit_store.db)        │
                                          └───────────────────────────┘
```

---

## 🚀 Quickstart: Running with Docker Compose

To build and start both the backend analytical engine and frontend SPA:

```bash
docker compose up --build -d
```

### Accessing the Applications:
* **Frontend SPA:** [http://localhost:3000](http://localhost:3000)
* **Backend REST API:** [http://localhost:8000/api](http://localhost:8000/api)
* **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Healthcheck:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📦 Container Specifications

### 1. Backend (`docker/Dockerfile.backend`)
* **Base Image:** `python:3.11-slim`
* **Analytical Core:** Loads and caches the 102k+ canonical works parquet dataset into memory on startup.
* **Persistent Audit Store:** Mounts `mplads_audit_data` volume at `/app/backend/data` to ensure AC-19 review checklist sign-offs and auditor notes survive container rebuilds.
* **Healthcheck:** Queries `/api/health` every 30s.

### 2. Frontend (`docker/Dockerfile.frontend`)
* **Stage 1 (Builder):** Uses `node:20-alpine` with `pnpm` to compile TypeScript and bundle assets with Vite.
* **Stage 2 (Server):** Uses lightweight `nginx:alpine` to serve static assets and proxy `/api/` traffic to the backend container over internal Docker DNS (`http://backend:8000`).

---

## 🛠️ Operational Commands

### View Container Logs:
```bash
# View unified logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# View frontend logs only
docker compose logs -f frontend
```

### Stop the Containers:
```bash
docker compose down
```

### Reset / Purge SQLite Persistent Data:
```bash
docker compose down -v
```

### Run Backend Unit Tests Inside Container:
```bash
docker compose exec backend pytest backend/tests/
```
