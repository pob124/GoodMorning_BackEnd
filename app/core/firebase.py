# app/core/firebase.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.core.config import settings
import firebase_admin
from firebase_admin import credentials, auth
import logging
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2PasswordBearer 스키마 정의
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
    description="Firebase ID Token을 입력하세요"
)

# Firebase Admin SDK 초기화
def initialize_firebase():
    try:
        # 이미 초기화되어 있는지 확인
        firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized")
    except ValueError:
        # 초기화되어 있지 않은 경우에만 초기화
        logger.info("Initializing Firebase Admin SDK")
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 토큰 검증 함수
async def verify_token(token: str):
    try:
        logger.info(f"Verifying token: {token[:20]}...")
        
        # 시간 동기화 문제 해결을 위해 check_revoked=False로 설정하고
        # 시간 검증을 더 관대하게 처리
        try:
            decoded_token = auth.verify_id_token(token, check_revoked=False)
        except Exception as e:
            if "Token used too early" in str(e):
                logger.warning(f"Token timing issue detected, retrying in 2 seconds: {str(e)}")
                time.sleep(2)
                decoded_token = auth.verify_id_token(token, check_revoked=False)
            else:
                raise e
                
        logger.info(f"Token verified successfully. UID: {decoded_token.get('uid')}")
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 현재 사용자 ID 가져오기
async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """
    Firebase ID Token에서 현재 사용자 ID를 추출합니다.
    
    **인증 필요**: SwaggerUI의 Authorize 버튼을 사용하여 Firebase ID Token 입력
    - Username: 아무 값 (예: "user")
    - Password: Firebase ID Token
    
    Returns:
        str: Firebase UID
    """
    try:
        logger.info(f"Getting current user ID from token: {token[:20]}...")
        
        # 시간 동기화 문제 해결을 위한 재시도 로직
        try:
            decoded_token = auth.verify_id_token(token, check_revoked=False)
        except Exception as e:
            if "Token used too early" in str(e):
                logger.warning(f"Token timing issue detected, retrying in 2 seconds: {str(e)}")
                time.sleep(2)
                decoded_token = auth.verify_id_token(token, check_revoked=False)
            else:
                raise e
                
        uid = decoded_token["uid"]
        logger.info(f"Current user ID: {uid}")
        return uid
    except Exception as e:
        logger.error(f"Failed to get current user ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )