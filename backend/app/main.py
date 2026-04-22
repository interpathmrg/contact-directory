import logging

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import admin, auth, contacts, import_export, labels

settings = get_settings()

# ---------------------------------------------------------------------------
# Logging estructurado (JSON en producción, pretty en desarrollo)
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
        if settings.environment == "production"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Contact Directory API",
    version="1.0.0",
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url="/api/redoc" if settings.environment != "production" else None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router,          prefix="/api")
app.include_router(contacts.router,      prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(labels.router,        prefix="/api")
app.include_router(admin.router,         prefix="/api")


# ---------------------------------------------------------------------------
# Health / Ready  (K8s probes + Docker healthcheck)
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"], include_in_schema=False)
async def ready() -> dict:
    """Readiness probe: verifica conexión a la BD."""
    try:
        import sqlalchemy
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        log.error("readiness_check_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
