from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import checkout, health, me, webhooks

settings = get_settings()

app = FastAPI(title="Antigravity API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(me.router, prefix="/api", tags=["auth"])
app.include_router(checkout.router, prefix="/api", tags=["checkout"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
