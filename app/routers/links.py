from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app import models, schemas
from app.dependencies import get_db
import secrets

SHORT_KEY_NUM_BYTES = 6
NUM_KEY_GENERATION_ATTEMPTS = 5

router = APIRouter()

@router.post("/links", response_model=schemas.LinkRead, status_code=status.HTTP_201_CREATED)
def create_link(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    for _ in range(NUM_KEY_GENERATION_ATTEMPTS):
        short_key = secrets.token_urlsafe(SHORT_KEY_NUM_BYTES)
        exists = db.query(models.Link).filter_by(short_key=short_key).first()
        if not exists:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate a unique short key.")

    db_link = models.Link(short_key=short_key, target_url=str(link.target_url))
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

@router.get("/{short_key}")
def redirect_link(short_key: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short_key=short_key).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    link.clicks += 1
    db.commit()
    return RedirectResponse(url=link.target_url)

@router.get("/links/{short_key}/stats", response_model=schemas.LinkStats)
def link_stats(short_key: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter_by(short_key=short_key).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    return schemas.LinkStats(short_key=link.short_key, clicks=link.clicks)