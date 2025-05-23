from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from app.core.firebase import verify_token, get_db, auth
from app.models.user_models import Token, TokenData, UserDB
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["인증"],
    responses={404: {"description": "Not found"}},
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class LoginRequest(BaseModel):
    token: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    decoded_token = await verify_token(token)
    if decoded_token is None:
        raise credentials_exception
        
    token_data = TokenData(firebase_uid=decoded_token.get("uid"))
    if token_data.firebase_uid is None:
        raise credentials_exception
        
    return token_data

@router.post("/login", response_model=Token)
async def login(request: LoginRequest = Body(...), db: Session = Depends(get_db)):
    """Firebase UID로 로그인"""
    try:
        logger.info(f"Login attempt with token: {request.token}")
        
        # UID로 사용자 정보 가져오기
        user = auth.get_user(request.token)
        logger.info(f"Firebase user found: {user.uid}")
        
        # 사용자 정보 확인 및 생성
        db_user = db.query(UserDB).filter(UserDB.firebase_uid == user.uid).first()
        if not db_user:
            logger.info("Creating new user in database")
            # 새 사용자 생성
            new_user = UserDB(
                firebase_uid=user.uid,
                email=user.email or "",
                nickname=user.display_name or ""
            )
            db.add(new_user)
            db.commit()
            logger.info("New user created successfully")
        
        # 커스텀 토큰 생성
        custom_token = auth.create_custom_token(user.uid)
        logger.info("Custom token created successfully")
        
        return Token(
            access_token=custom_token.decode(),
            token_type="bearer"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) 