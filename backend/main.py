from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from routers.auth import router as auth_router
from routers.properties import router as properties_router
from routers.files import router as files_router
from routers.permissions import router as permissions_router
from routers.fees import router as fees_router
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
app.include_router(properties_router)
app.include_router(files_router)
app.include_router(permissions_router)
app.include_router(fees_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "入力内容に誤りがあります",
                "detail": {"errors": errors},
            }
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    # If the 404 was raised via HTTPException with dict detail (e.g. from auth code),
    # delegate to the HTTPException handler by re-raising
    if isinstance(exc, HTTPException) and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=404,
            content={"error": exc.detail},
        )
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "リソースが見つかりません",
                "detail": {"path": str(request.url)},
            }
        },
    )


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    if isinstance(exc, HTTPException) and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=401,
            content={"error": exc.detail},
        )
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "UNAUTHORIZED",
                "message": "認証が必要です",
            }
        },
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    if isinstance(exc, HTTPException) and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=403,
            content={"error": exc.detail},
        )
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "FORBIDDEN",
                "message": "権限がありません",
            }
        },
    )


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
    return {"data": {"status": "ok"}, "message": "OK"}
