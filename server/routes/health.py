"""
Health check routes
"""
from fastapi import APIRouter
from database import DatabaseConnection

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "GI Claim Assistance API"}


@router.get("/db-check")
async def database_check():
    """Check database connectivity"""
    try:
        with DatabaseConnection.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return {"status": "connected", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
