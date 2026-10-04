"""
Main application server for AISYS RFID Library Management Solution.
Mounts all REST API routers, serves static single-page application frontend,
and initializes database migrations on startup.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import get_config
from src.core.database import db_manager
from src.core.logger import logger
from data.seeds.seed_data import seed_database

# Import API Routers
from src.api.routes_auth import router as auth_router
from src.api.routes_catalog import router as catalog_router
from src.api.routes_circulation import router as circulation_router
from src.api.routes_members import router as members_router
from src.api.routes_rfid import router as rfid_router
from src.api.routes_inventory import router as inventory_router
from src.api.routes_gate import router as gate_router
from src.api.routes_migration import router as migration_router
from src.api.routes_reports import router as reports_router
from src.api.routes_admin import router as admin_router
from src.api.routes_ncip_sip2 import router as interop_router

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "src" / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Apply database migrations and ensure seeds exist
    logger.info("AISYS System booting up...")
    db_manager.apply_migrations()
    seed_database()
    logger.info("AISYS System initialization complete. Ready to serve requests.")
    yield
    # Shutdown
    logger.info("AISYS System shutting down cleanly.")

app = FastAPI(
    title="AISYS RFID Library Management System",
    description="High-integrity RFID library solution with non-destructive ILMS integration and offline lifecycle support.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include All Routers
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(circulation_router)
app.include_router(members_router)
app.include_router(rfid_router)
app.include_router(inventory_router)
app.include_router(gate_router)
app.include_router(migration_router)
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(interop_router)

# Mount Static Files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "AISYS RFID Library Solution API is running. Navigate to /docs for API swagger."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
