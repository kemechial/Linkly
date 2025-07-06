from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.routers import links, auth
from app.dependencies import get_db
from app import crud

app = FastAPI(title="Linkly API")

app.include_router(auth.router)
app.include_router(links.router)


@app.get("/{short_key}")
def redirect_to_target_url(
    short_key: str,
    db: Session = Depends(get_db)
):
    db_link = crud.get_link_and_increment_clicks(db, short_key=short_key)
    if db_link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return RedirectResponse(url=db_link.target_url)