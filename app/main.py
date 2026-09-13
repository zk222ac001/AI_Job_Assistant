import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import alerts, analysis, applications, candidates, discovery, email_monitor, health, interviews, jobs, resumes
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.logging import configure_logging
configure_logging(); logger = logging.getLogger(__name__); settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.3.0", docs_url="/docs" if settings.app_env != "production" else None, redoc_url="/redoc" if settings.app_env != "production" else None)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
@app.exception_handler(NotFoundError)
async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse: return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.detail})
@app.exception_handler(ValueError)
async def handle_value_error(_: Request, exc: ValueError) -> JSONResponse: return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})
@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path); return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})
for router in [health.router, candidates.router, jobs.router, applications.router, resumes.router, analysis.router, discovery.router, alerts.router, email_monitor.router, interviews.router]:
    app.include_router(router, prefix="" if router is health.router else settings.api_v1_prefix)
