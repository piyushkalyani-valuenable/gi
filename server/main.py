from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import chat_router
from config.settings import settings
from database.setup import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Create tables if they don't exist
    print("🚀 Starting up...")
    try:
        create_tables()
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="GI Claim Assistance API",
    description="Insurance Claim Assessment API with Gemini AI",
    version="2.0.0",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "GI Claim Assistance API is running",
        "version": "2.0.0",
        "status": "healthy"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "gemini_configured": bool(settings.gemini_api_key)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
