from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.firebase import get_db, get_current_user_id
from app.models.user_models import UserDB
from app.schemas.user import UserProfile
from typing import Optional, List
import json

# 한국어 지원을 위한 커스텀 JSON Response
class UnicodeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,  # 한국어 유니코드 문자 그대로 출력
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

router = APIRouter(
    prefix="/users",
    tags=["사용자"],
    responses={404: {"description": "Not found"}},
)

# [프로필] 현재 사용자의 프로필 정보 조회
@router.get("/me", summary="내 프로필 조회")
async def get_my_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """현재 로그인한 사용자의 프로필을 조회합니다."""
    user = db.query(UserDB).filter(UserDB.firebase_uid == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile_data = {
        "uid": user.firebase_uid,
        "nickname": user.name,
        "bio": user.bio,
        "profileImageUrl": user.profile_picture,
        "likes": user.likes or 0
    }
    
    return UnicodeJSONResponse(content=profile_data)

# [프로필] 특정 사용자의 프로필 정보 조회
@router.get("/profile/{uid}", summary="사용자 프로필 조회")
async def get_user_profile(
    uid: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """특정 사용자의 프로필을 조회합니다."""
    user = db.query(UserDB).filter(UserDB.firebase_uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile_data = {
        "uid": user.firebase_uid,
        "nickname": user.name,
        "bio": user.bio,
        "profileImageUrl": user.profile_picture,
        "likes": user.likes or 0
    }
    
    return UnicodeJSONResponse(content=profile_data)

# [프로필] 프로필 정보 수정
@router.patch("/profile", summary="프로필 수정")
async def update_user_profile(
    update_data: dict = Body(...),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """사용자의 bio 및 nickname 정보를 수정합니다."""
    user = db.query(UserDB).filter(UserDB.firebase_uid == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 업데이트 처리
    updated_fields = []
    if "bio" in update_data:
        user.bio = update_data["bio"]
        updated_fields.append("bio")
    if "nickname" in update_data:
        user.name = update_data["nickname"]
        updated_fields.append("nickname")
    if "profileImageUrl" in update_data:
        user.profile_picture = update_data["profileImageUrl"]
        updated_fields.append("profileImageUrl")

    db.commit()
    db.refresh(user)

    response_data = {
        "uid": user.firebase_uid,
        "nickname": user.name,
        "bio": user.bio,
        "profileImageUrl": user.profile_picture,
        "likes": user.likes or 0,
        "updated_fields": updated_fields,
        "message": f"프로필이 성공적으로 업데이트되었습니다. 수정된 필드: {', '.join(updated_fields)}"
    }
    
    return UnicodeJSONResponse(content=response_data)

# [프로필] 전체 사용자 목록 조회
@router.get("/", summary="사용자 목록 조회")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """사용자 목록을 조회합니다."""
    users = db.query(UserDB).offset(skip).limit(limit).all()
    
    users_data = [
        {
            "uid": user.firebase_uid,
            "nickname": user.name,
            "bio": user.bio,
            "profileImageUrl": user.profile_picture,
            "likes": user.likes or 0
        }
        for user in users
    ]
    
    return UnicodeJSONResponse(content=users_data)