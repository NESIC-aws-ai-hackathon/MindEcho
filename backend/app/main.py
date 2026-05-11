from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.cognitive.router import router as cognitive_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.data.router import router as data_router
from app.media.router import router as media_router

app = FastAPI(
    title="MindEcho API",
    description="感情言語化支援サービス",
    version="0.1.0",
    debug=settings.app_debug,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(media_router)
app.include_router(cognitive_router)


# Global exception handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.error_message, "details": exc.details}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "サーバー内部エラーが発生しました",
                "details": [],
            }
        },
    )


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
