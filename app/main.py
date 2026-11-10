"""FastAPI application entry point. Wiring only; no business logic here."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import auth, budgets, expenses


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Personal finance backend: budgets, reports, anomaly "
        "detection, forecasting, OCR receipts and AI recommendations.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(auth.router)
    app.include_router(expenses.router)
    app.include_router(budgets.router)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        """Liveness check. Also shows which optional integrations are enabled."""
        return {
            "status": "ok",
            "ai_provider": settings.ai_provider,
            "ocr_provider": settings.ocr_provider,
        }

    return app


app = create_app()