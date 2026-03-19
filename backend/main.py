from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers.auth import router as auth_router
from auth import get_current_user, require_role
from models.user import User

app = FastAPI(title="自治体財産管理システム", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/admin-only")
def admin_only_endpoint(current_user: User = Depends(get_current_user)):
    require_role(current_user, ["admin"])
    return {"data": {"message": "admin access"}}


app.include_router(auth_router)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": detail},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "ERROR", "message": str(detail)}},
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
