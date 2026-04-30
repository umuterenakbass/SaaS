from fastapi import FastAPI

from app.api.v1.router import api_router_v1
from app.core.config import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(api_router_v1, prefix=settings.api_v1_prefix)
    return app


app = create_app()
