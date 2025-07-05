from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app import models, schemas, auth, crud
from app.dependencies import get_db

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
        return crud.create_link(db=db, link_in=link, user_id=current_user.id)
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
    return schemas.LinkStats(short_key=link.short_key, clicks=link.clicks)