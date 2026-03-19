"""初期データ作成スクリプト - 管理者アカウントとテストユーザーを作成する

Usage:
    cd backend
    python seed.py
"""

from database import SessionLocal, engine, Base
from models.user import User
from auth import hash_password


def seed():
    # テーブルが存在しない場合は作成
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 既存データ確認
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("管理者アカウントは既に存在します: admin")
            return

        # 管理者アカウント
        admin = User(
            username="admin",
            hashed_password=hash_password("Admin123"),
            display_name="システム管理者",
            role="admin",
            department="財政課",
        )
        db.add(admin)

        # 一般職員
        staff1 = User(
            username="tanaka",
            hashed_password=hash_password("Tanaka123"),
            display_name="田中太郎",
            role="staff",
            department="財産管理担当",
        )
        db.add(staff1)

        # 閲覧専用
        viewer = User(
            username="sato",
            hashed_password=hash_password("Sato12345"),
            display_name="佐藤花子",
            role="viewer",
            department="監査室",
        )
        db.add(viewer)

        db.commit()
        print("初期データを作成しました:")
        print("  管理者: admin / Admin123")
        print("  職員: tanaka / Tanaka123")
        print("  閲覧: sato / Sato12345")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
