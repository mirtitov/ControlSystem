from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import batches, products, tasks, webhooks, analytics
from src.database import engine, Base
from src.services.cache_service import cache_service
import asyncio

# Rate limiting (optional - can be enabled if needed)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False

app = FastAPI(
    title="Production Control System API",
    description="Система контроля заданий на выпуск продукции",
    version="1.0.0"
)

# Rate limiting (optional)
if RATE_LIMITING_AVAILABLE:
    try:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    except Exception as e:
        print(f"⚠️  Rate limiting not configured: {e}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(batches.router)
app.include_router(products.router)
app.include_router(tasks.router)
app.include_router(webhooks.router)
app.include_router(analytics.router)


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    # Connect to Redis
    await cache_service.connect()
    
    # Create database tables (in production, use Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await cache_service.disconnect()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Production Control System API",
        "version": "1.0.0",
        "docs": "/docs"
    }
