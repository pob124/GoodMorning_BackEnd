from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database_models import User as models
from app.core import get_settings
from app.auth.utils import get_current_user
from app.core.database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
settings = get_settings()

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: models = Depends(get_current_user)):
    """현재 인증된 사용자 정보를 반환합니다."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "username": current_user.username,
        "is_active": current_user.is_active
    }

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