from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.routers import links, auth
from app.dependencies import get_db
from app import crud
from app.services.redis_cache import link_cache

from . import models
from .database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Linkly API")

app.include_router(auth.router)
app.include_router(links.router)

@app.get("/{short_key}")
def redirect_to_target_url(
    short_key: str,
    db: Session = Depends(get_db)
):
    # Try Redis cache first
    cached_link = link_cache.get_link(short_key)
    
    if cached_link:
        # Found in cache - increment clicks in Redis only
        link_cache.increment_clicks(short_key)
        return RedirectResponse(url=cached_link["target_url"])
    
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
    
    return RedirectResponse(url=db_link.target_url)