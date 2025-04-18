from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database_models import User as models
from app.core import get_settings
from app.auth.utils import get_current_user, verify_token
from app.core.database import get_db
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    # 추가 프로필 필드
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(token_data: dict = Depends(verify_token)):
    """현재 인증된 사용자 정보를 반환합니다. DB에 저장하지 않고 토큰 정보만 사용."""
    try:
        # 토큰에서 직접 사용자 정보 반환 (DB 조회 없음)
        return {
            "id": token_data["firebase_uid"],  # Firebase UID를 ID로 사용
            "email": token_data["email"],
            "name": token_data["name"],
            "username": None,  # Firebase에서 제공하지 않는 정보는 기본값 사용
            "is_active": True,
            "profile_picture": None,
            "bio": None,
            "phone_number": None,
            "location": None,
            "gender": None,
            "birth_date": None,
            "last_login_at": None
        }
    except Exception as e:
        logger.error(f"Error in read_users_me: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보를 가져오는 중 오류 발생: {str(e)}"
        )

@router.post("/users/me", response_model=UserResponse)
async def update_users_me(
    user_update: UserUpdate,
    current_user: models = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자 정보를 업데이트합니다."""
    # 업데이트할 필드만 처리
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "username": current_user.username,
        "is_active": current_user.is_active
    }

@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_users_me(
    current_user: models = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자 계정을 비활성화합니다."""
    current_user.is_active = False
    db.commit()
    return {"detail": "계정이 비활성화되었습니다"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "app_name": settings.APP_NAME} 