# app/core/firebase.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.core.config import settings
import firebase_admin
from firebase_admin import credentials, auth
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        token = credentials.credentials
        logger.info(f"Verifying token: {token[:20]}...")
        decoded_token = auth.verify_id_token(token)
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
async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        token = credentials.credentials
        logger.info(f"Getting current user ID from token: {token[:20]}...")
        decoded_token = auth.verify_id_token(token)
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