import secrets
from sqlalchemy.orm import Session
from app import models, schemas

SHORT_KEY_NUM_BYTES = 6
NUM_KEY_GENERATION_ATTEMPTS = 5

def create_link(db: Session, link_in: schemas.LinkCreate, user_id: int) -> models.Link:
    for _ in range(NUM_KEY_GENERATION_ATTEMPTS):
        short_key = secrets.token_urlsafe(SHORT_KEY_NUM_BYTES)
        exists = db.query(models.Link).filter_by(short_key=short_key).first()
        if not exists:
            break
    else:
        raise Exception("Could not generate a unique short key.")

    db_link = models.Link(
        short_key=short_key,
        target_url=str(link_in.target_url),
        owner_id=user_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def get_user_links(db: Session, user_id: int):
    return db.query(models.Link).filter_by(owner_id=user_id).all()

def get_link_stats(db: Session, short_key: str):
    link = db.query(models.Link).filter_by(short_key=short_key).first()
    if not link:
        return None
    return link




