from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.v1.router import api_router
from app.db.database import Base, engine
from app.core.logging import logger
from app.core.rate_limiter import limiter

# Create FastAPI application
app = FastAPI(
    title="DocMind AI",
    description="AI-powered document analysis and retrieval system",
    version="2.0.0",
)

# Register Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected internal server error occurred."},
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DocMind AI application")
    Base.metadata.create_all(bind=engine)
    logger.info("Database models initialized")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down DocMind AI application")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Instrument Prometheus
Instrumentator().instrument(app).expose(app)


# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to DocMind AI"}