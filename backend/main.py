from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings
from backend.models.schemas import ErrorResponse
from backend.api.v1.routes import router as api_v1_router
from backend.utils.logging import set_request_id, logger

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Voice AI Knowledge Assistant",
    version="1.0.0"
)

# CORS Middleware (Allow future PWA to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID Correlation Middleware
class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID")
        set_request_id(req_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = set_request_id()
        return response

app.add_middleware(RequestCorrelationMiddleware)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    err = ErrorResponse(
        error_code="internal_server_error",
        message="An unexpected error occurred.",
        details={"raw_message": str(exc)}
    )
    return JSONResponse(
        status_code=500,
        content=err.model_dump()
    )

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
