from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    short_key = Column(String(20), unique=True, index=True, nullable=False)
    target_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    clicks = Column(Integer, default=0)  # <--- add this line!

if __name__ == "__main__":
    from .database import engine
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")