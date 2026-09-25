"""
FastAPI Server Entrypoint for MPLADS Autonomous Audit & Intelligence Platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import BASE_DIR, DEBUG
from backend.routes.actions import router as actions_router
from backend.routes.analytics import router as analytics_router
from backend.routes.auth import router as auth_router
from backend.routes.compliance import router as compliance_router
from backend.routes.detectors import router as detectors_router
from backend.routes.districts import router as districts_router
from backend.routes.dossier import router as dossier_router
from backend.routes.duplicates import router as duplicates_router
from backend.routes.investigations import router as investigations_router
from backend.routes.map import router as map_router
from backend.routes.mps import router as mps_router
from backend.routes.overview import router as overview_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.vendors import router as vendors_router
from backend.routes.works import router as works_router
from backend.services.data_service import DataService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly initialize and warm in-memory cache
    print("Initializing MPLADS analytical core on server startup...")
    DataService.get_instance()
    yield
    print("Shutting down MPLADS backend...")


app = FastAPI(
    title="MPLADS Autonomous Analytical & Intelligence Core API",
    description="Full-stack e-Governance, Anomaly Detection & Review Prioritization Platform (SIH PS102)",
    version="1.0.0",
    lifespan=lifespan,
    debug=DEBUG,
)

# CORS Middleware allowing local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(overview_router, prefix="/api")
app.include_router(map_router, prefix="/api")
app.include_router(mps_router, prefix="/api")
app.include_router(districts_router, prefix="/api")
app.include_router(vendors_router, prefix="/api")
app.include_router(works_router, prefix="/api")
app.include_router(dossier_router, prefix="/api")
app.include_router(detectors_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(duplicates_router, prefix="/api")
app.include_router(investigations_router, prefix="/api")
app.include_router(compliance_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "MPLADS Autonomous Analytical Platform",
        "version": "1.0.0",
    }


# Serve static built frontend SPA if available
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from starlette.responses import FileResponse, JSONResponse

    @app.exception_handler(StarletteHTTPException)
    async def spa_fallback_handler(request, exc):
        if exc.status_code == 404 and not request.url.path.startswith("/api"):
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
