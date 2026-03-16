from fastapi import FastAPI
from app.api.departments import router
from app.config import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(router, prefix="/api/v1")
