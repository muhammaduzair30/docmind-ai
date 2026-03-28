from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
        db_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def revoke(self, token: str) -> bool:
        db_token = self.get_by_token(token)
        if db_token and not db_token.is_revoked:
            db_token.is_revoked = True
            self.db.commit()
            return True
        return False

    def revoke_all_for_user(self, user_id: int) -> None:
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id, 
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        self.db.commit()
