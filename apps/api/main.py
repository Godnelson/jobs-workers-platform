from fastapi import FastAPI

from apps.api.logging import configure_logging
from apps.api.settings import load_settings
from apps.api.db import init_engine
from apps.api.routes.jobs import router as jobs_router


def create_app() -> FastAPI:
    settings = load_settings()
    configure_logging(settings.log_level)

    # DB init
    init_engine(settings.database_url)

    app = FastAPI(title="Jobs/Workers Platform", version="0.1.0")
    app.include_router(jobs_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
