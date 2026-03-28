from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user_schema import UserLogin
from app.core.security import (
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_token,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.repositories.refresh_token_repository import RefreshTokenRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.token_repo = RefreshTokenRepository(db)

    def login(self, user_login: UserLogin) -> Tuple[str, str]:
        user = self.db.query(User).filter(User.username == user_login.username).first()
        if not user or not verify_password(user_login.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )

        return self._issue_tokens(user.id)

    def refresh(self, raw_refresh_token: str) -> Tuple[str, str]:
        hashed_token = hash_token(raw_refresh_token)
        db_token = self.token_repo.get_by_token(hashed_token)

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check if revoked (Reuse detection)
        if db_token.is_revoked:
            # Token was reused! Security measure: revoke ALL sessions for this user.
            self.token_repo.revoke_all_for_user(db_token.user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Refresh token reused. All sessions revoked."
            )

        # Check if expired
        if db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        # Token is valid: Revoke it and issue new ones (Rotation)
        self.token_repo.revoke(hashed_token)
        return self._issue_tokens(db_token.user_id)

    def logout(self, raw_refresh_token: str):
        hashed_token = hash_token(raw_refresh_token)
        self.token_repo.revoke(hashed_token)

    def _issue_tokens(self, user_id: int) -> Tuple[str, str]:
        access_token = create_access_token({"user_id": user_id})
        raw_refresh_token = generate_refresh_token()
        hashed_refresh_token = hash_token(raw_refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        self.token_repo.create(
            user_id=user_id,
            token=hashed_refresh_token,
            expires_at=expires_at
        )
        
        return access_token, raw_refresh_token
