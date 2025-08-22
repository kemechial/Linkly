from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.routers import links, auth
from app.dependencies import get_db
from app import crud, models
from app.services.redis_cache import link_cache
from app.database import engine
from app.config import settings
from app.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("main")

# models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    """Initialize database tables on startup"""
    logger.info("Starting up Linkly API...")
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
    logger.info(f"Application started in {settings.environment} mode")

@app.on_event("shutdown")
def on_shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down Linkly API...")

app.include_router(auth.router)
app.include_router(links.router)

@app.get("/{short_key}")
def redirect_to_target_url(
    short_key: str,
    db: Session = Depends(get_db)
):
    """
    Redirect to the target URL for a given short key.
    Implements caching with Redis for performance.
    """
    try:
        # Validate short_key format
        if not short_key or len(short_key) > 20:
            raise HTTPException(status_code=400, detail="Invalid short key format")
        
        # Try Redis cache first
        cached_link = link_cache.get_link(short_key)
        
        if cached_link:
            # Found in cache - increment clicks in Redis only
            link_cache.increment_clicks(short_key)
            return RedirectResponse(url=cached_link["target_url"], status_code=307)
        
        # Not in cache, get from database
        db_link = crud.get_link_and_increment_clicks(db, short_key=short_key)
        
        if db_link is None:
            raise HTTPException(status_code=404, detail="Link not found")
        
        # Cache for next time
        link_cache.set_link(short_key, db_link.target_url)
        
        # Initialize click counter in Redis with current DB value
        current_clicks = link_cache.get_clicks(short_key)
        if current_clicks == 0:
            # Set initial click count from DB
            for _ in range(db_link.clicks):
                link_cache.increment_clicks(short_key)
        
        return RedirectResponse(url=db_link.target_url, status_code=307)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors and return generic error
        logger.error(f"Unexpected error in redirect_to_target_url for key '{short_key}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "linkly-api"}