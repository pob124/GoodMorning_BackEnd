from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None

# [프로필] 내 프로필 정보 조회
@router.get("/me")
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    return await UserService.get_user_profile(db, current_user_id)

# [프로필] 특정 사용자의 프로필 정보 조회
@router.get("/profile/{uid}")
async def get_user_profile(
    uid: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    return await UserService.get_user_profile(db, uid)

# [프로필] 내 프로필 정보 수정
@router.put("/me")
async def update_my_profile(
    profile: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    return await UserService.update_user_profile(
        db=db,
        user_id=current_user_id,
        nickname=profile.nickname,
        profile_image=profile.profile_image,
        bio=profile.bio
    )

# [프로필] 전체 사용자 목록 조회
@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    return await UserService.get_all_users(db, skip=skip, limit=limit) 