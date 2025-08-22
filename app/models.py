from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # One-to-many relationship: a User has many Links
    links = relationship("Link", back_populates="owner")

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    short_key = Column(String(20), unique=True, index=True, nullable=False)
    target_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    clicks = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Many-to-one relationship: a Link is owned by a User
    owner = relationship("User", back_populates="links")

if __name__ == "__main__":
    from app.database import engine
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")