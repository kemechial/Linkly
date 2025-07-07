from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app import models, schemas, auth, crud
from app.dependencies import get_db
from app.services.redis_cache import link_cache

router = APIRouter(
    prefix="/links",
    tags=["links"]
)

@router.post("/", response_model=schemas.LinkRead, status_code=status.HTTP_201_CREATED)
def create_link(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        db_link = crud.create_link(db=db, link_in=link, user_id=current_user.id)
        
        # Cache the new link immediately
        link_cache.set_link(db_link.short_key, db_link.target_url)
        
        return db_link
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=list[schemas.LinkRead])
def my_links(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.get_user_links(db, current_user.id)

@router.get("/{short_key}/stats", response_model=schemas.LinkStats)
def link_stats(
    short_key: str,
    db: Session = Depends(get_db),
):
    link = crud.get_link_stats(db, short_key)
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    # Get click count from Redis
    redis_clicks = link_cache.get_clicks(short_key)
    
    # Use Redis count if available (it's more up-to-date), otherwise use DB
    total_clicks = redis_clicks if redis_clicks > 0 else link.clicks
    
    return schemas.LinkStats(short_key=link.short_key, clicks=total_clicks)