"""
Service layer for URL shortening business logic
"""
import secrets
import validators
from typing import List, Optional
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models, schemas
from app.services.redis_cache import link_cache
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Malicious domain blacklist (in production, use external service)
BLOCKED_DOMAINS = {
    'malware.com', 'phishing.net', 'spam.org'
}

class URLValidationError(Exception):
    pass

class LinkService:
    """Business logic for link management"""
    
    def __init__(self):
        self.short_key_length = 8
        self.max_generation_attempts = 10
    
    def validate_url(self, url: str) -> str:
        """Validate and normalize URL"""
        if len(url) > settings.max_url_length:
            raise URLValidationError("URL too long")
        
        if not validators.url(url):
            raise URLValidationError("Invalid URL format")
        
        parsed = urlparse(url)
        if parsed.netloc.lower() in BLOCKED_DOMAINS:
            raise URLValidationError("URL is blocked")
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def generate_short_key(self, db: Session) -> str:
        """Generate unique short key"""
        for _ in range(self.max_generation_attempts):
            short_key = secrets.token_urlsafe(self.short_key_length)[:self.short_key_length]
            
            # Check database for collision
            existing = db.query(models.Link).filter_by(short_key=short_key).first()
            if not existing:
                return short_key
        
        raise Exception("Could not generate unique short key")
    
    def create_link(self, db: Session, link_data: schemas.LinkCreate, user_id: int) -> models.Link:
        """Create a new short link"""
        try:
            # Validate URL
            validated_url = self.validate_url(str(link_data.target_url))
            
            # Check for existing link by this user
            existing_link = db.query(models.Link).filter_by(
                target_url=validated_url,
                owner_id=user_id
            ).first()
            
            if existing_link:
                logger.info(f"Returning existing link for {validated_url}")
                return existing_link
            
            # Generate short key
            short_key = self.generate_short_key(db)
            
            # Create link
            db_link = models.Link(
                short_key=short_key,
                target_url=validated_url,
                owner_id=user_id
            )
            
            db.add(db_link)
            db.commit()
            db.refresh(db_link)
            
            # Cache immediately
            link_cache.set_link(short_key, validated_url)
            
            logger.info(f"Created link {short_key} -> {validated_url}")
            return db_link
            
        except URLValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating link: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create link"
            )
    
    def get_user_links(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Link]:
        """Get paginated user links"""
        return db.query(models.Link).filter_by(owner_id=user_id).offset(skip).limit(limit).all()
    
    def get_link_stats(self, db: Session, short_key: str) -> Optional[dict]:
        """Get link statistics"""
        link = db.query(models.Link).filter_by(short_key=short_key).first()
        if not link:
            return None
        
        # Get real-time clicks from Redis
        redis_clicks = link_cache.get_clicks(short_key)
        total_clicks = max(redis_clicks, link.clicks)
        
        return {
            "short_key": link.short_key,
            "target_url": link.target_url,
            "clicks": total_clicks,
            "created_at": link.created_at,
            "owner_id": link.owner_id
        }
    
    def redirect_link(self, db: Session, short_key: str) -> str:
        """Handle link redirection and click tracking"""
        # Try cache first
        cached_link = link_cache.get_link(short_key)
        
        if cached_link:
            # Increment clicks in Redis
            link_cache.increment_clicks(short_key)
            return cached_link["target_url"]
        
        # Get from database
        link = db.query(models.Link).filter_by(short_key=short_key).first()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        # Cache for future requests
        link_cache.set_link(short_key, link.target_url)
        
        # Increment clicks
        link_cache.increment_clicks(short_key)
        
        # Periodically sync with database (every 10 clicks)
        redis_clicks = link_cache.get_clicks(short_key)
        if redis_clicks % 10 == 0:
            link.clicks = redis_clicks
            db.commit()
        
        return link.target_url
    
    def delete_link(self, db: Session, short_key: str, user_id: int) -> bool:
        """Delete a user's link"""
        link = db.query(models.Link).filter_by(
            short_key=short_key,
            owner_id=user_id
        ).first()
        
        if not link:
            return False
        
        # Remove from cache
        link_cache.delete_link(short_key)
        
        # Delete from database
        db.delete(link)
        db.commit()
        
        logger.info(f"Deleted link {short_key}")
        return True


# Global service instance
link_service = LinkService()
