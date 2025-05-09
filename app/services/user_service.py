from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import HTTPException
from typing import Dict, Any

class UserService:
    @staticmethod
    def _format_profile_response(user: User) -> Dict[Any, Any]:
        return {
            "uid": user.id,
            "nickname": user.nickname,
            "bio": user.bio,
            "profileImageUrl": user.profile_image,
            "likes": user.likes
        }

    @staticmethod
    async def get_user_profile(db: Session, user_id: str) -> Dict[Any, Any]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserService._format_profile_response(user)

    @staticmethod
    async def update_user_profile(
        db: Session, 
        user_id: str, 
        nickname: str = None, 
        profile_image: str = None, 
        bio: str = None,
        likes: int = None
    ) -> Dict[Any, Any]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if nickname is not None:
            user.nickname = nickname
        if profile_image is not None:
            user.profile_image = profile_image
        if bio is not None:
            user.bio = bio
        if likes is not None:
            user.likes = likes
        
        db.commit()
        db.refresh(user)
        return UserService._format_profile_response(user)

    @staticmethod
    async def get_all_users(db: Session, skip: int = 0, limit: int = 100):
        users = db.query(User).offset(skip).limit(limit).all()
        return [UserService._format_profile_response(user) for user in users] 