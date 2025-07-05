from fastapi import FastAPI
from app.routers import links

app = FastAPI(title="Linkly API")

app.include_router(links.router)