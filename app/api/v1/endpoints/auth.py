from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.database import get_db
from typing import Optional

router = APIRouter()

# [인증] Firebase 토큰을 검증하여 사용자를 인증합니다.
@router.post("/verify-token")
async def verify_token(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    # Authorization 헤더가 없거나 Bearer 토큰이 아니면 401 에러 반환
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    # 토큰 추출 및 검증
    token = authorization.split(" ")[1]
    return await AuthService.verify_firebase_token(token, db) 