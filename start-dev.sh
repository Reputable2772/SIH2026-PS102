#!/usr/bin/env bash
set -e

echo "[*] Launching MPLADS Autonomous Intelligence Core in Live Dev Mode (Vite HMR + Uvicorn Reload)..."
podman-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --no-build

echo ""
echo "[✓] Active Dev Containers:"
podman ps --filter "name=mplads"

echo ""
echo "🌐 Frontend (Vite Dev + Instant HMR): http://localhost:5173"
echo "⚙️  Backend (FastAPI Core):            http://localhost:8000"
echo ""
echo "Hot-Reloading Status:"
echo "  • Frontend: Edits in frontend/src/ trigger instant sub-second HMR via WebSocket."
echo "  • Backend:  Edits in backend/ & detectors/ trigger Uvicorn WatchFiles reloads in ~2s."
echo "  • API:      All /api/* calls from port 5173 automatically proxy to the backend container."
