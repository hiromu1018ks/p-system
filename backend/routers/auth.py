from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, UserInfo
from auth import verify_password, create_access_token, decode_access_token, get_current_user
from audit import log_audit
from models.jwt_blacklist import JWTBlacklist

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    """ログイン - JWTトークンを発行する"""
    user = db.query(User).filter(
        User.username == request.username,
        User.is_deleted == False,
    ).first()

    if not user or not verify_password(request.password, user.hashed_password):
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.is_locked = True
            db.commit()
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "ユーザー名またはパスワードが正しくありません"},
        )

    if user.is_locked:
        raise HTTPException(
            status_code=403,
            detail={"code": "ACCOUNT_LOCKED", "message": "アカウントがロックされています。管理者に連絡してください"},
        )

    user.failed_login_count = 0
    db.commit()

    log_audit(
        db=db,
        user_id=user.id,
        action="LOGIN",
        target_table="m_user",
        target_id=user.id,
        ip_address=req.client.host if req.client else None,
    )

    token = create_access_token(user.id, user.username, user.role)

    return {
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
            },
        },
        "message": "OK",
    }


@router.post("/logout")
def logout(request_body: dict, db: Session = Depends(get_db)):
    """ログアウト - JWTをブラックリストに追加する"""
    token = request_body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token is required")

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    exp = payload.get("exp")

    blacklist_entry = JWTBlacklist(
        token_jti=jti,
        expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
    )
    db.add(blacklist_entry)
    db.commit()

    return {"data": None, "message": "ログアウトしました"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "role": current_user.role,
        },
        "message": "OK",
    }
