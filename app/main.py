from fastapi import FastAPI
from app.routers import links, auth

app = FastAPI(title="Linkly API")

app.include_router(auth.router)
app.include_router(links.router)