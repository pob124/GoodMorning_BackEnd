from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models import User, TokenData
from app.core.firebase import initialize_firebase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
firebase_app = initialize_firebase()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 테스트 환경에서는 가짜 사용자 반환
    return User(
        id="testuser123",
        email="test@example.com",
        name="Test User"
    ) 