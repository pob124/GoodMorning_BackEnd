from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.core import get_settings
from app.auth.utils import get_current_user

router = APIRouter()
settings = get_settings()

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/health")
async def health_check():
    return {"status": "healthy", "app_name": settings.APP_NAME} 