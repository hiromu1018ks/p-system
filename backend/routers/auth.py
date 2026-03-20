from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, UserInfo, UserCreateSchema
from auth import verify_password, create_access_token, decode_access_token, get_current_user, require_role, validate_password, hash_password
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


@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ユーザー一覧を取得する（管理者のみ）"""
    require_role(current_user, ["admin"])

    users = db.query(User).filter(User.is_deleted == False).all()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="LIST_USERS",
        target_table="m_user",
        ip_address=None,
    )

    return {
        "data": [
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.display_name,
                "role": u.role,
                "department": u.department,
                "is_locked": u.is_locked,
                "failed_login_count": u.failed_login_count,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "message": "OK",
    }


@router.post("/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ロックされたユーザーをアンロックする（管理者のみ）"""
    require_role(current_user, ["admin"])

    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False,
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"code": "USER_NOT_FOUND", "message": "ユーザーが見つかりません"},
        )

    before = {"is_locked": user.is_locked, "failed_login_count": user.failed_login_count}

    user.is_locked = False
    user.failed_login_count = 0

    after = {"is_locked": user.is_locked, "failed_login_count": user.failed_login_count}

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UNLOCK_USER",
        target_table="m_user",
        target_id=user.id,
        changed_fields=["is_locked", "failed_login_count"],
        before_value=before,
        after_value=after,
        ip_address=None,
    )

    db.commit()

    return {
        "data": {
            "id": user.id,
            "username": user.username,
            "is_locked": user.is_locked,
            "failed_login_count": user.failed_login_count,
        },
        "message": "ユーザーのロックを解除しました",
    }


@router.post("/users", status_code=201)
def create_user(
    body: UserCreateSchema,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新規ユーザーを作成する（管理者のみ）"""
    require_role(current_user, ["admin"])

    valid, msg = validate_password(body.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    existing = db.query(User).filter(
        User.username == body.username,
        User.is_deleted == False,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"code": "DUPLICATE_USERNAME", "message": "このユーザー名は既に使用されています"},
        )

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role=body.role,
        department=body.department,
    )
    db.add(user)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_USER",
        target_table="m_user",
        target_id=user.id,
        after_value={
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "department": user.department,
        },
        ip_address=req.client.host if req.client else None,
    )

    db.commit()

    return {
        "data": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "department": user.department,
        },
        "message": "ユーザーを作成しました",
    }
