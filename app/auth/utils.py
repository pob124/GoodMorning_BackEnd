from fastapi import Depends, HTTPException, status, Request as FastAPIRequest
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from app.models import UserDB as User 
from sqlalchemy.orm import Session
from app.services import get_db, initialize_firebase
import logging
from typing import Optional

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
firebase_app = initialize_firebase()

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # check_revoked=False 옵션 추가, 앱 검증 강제 옵션 추가
        decoded_token = auth.verify_id_token(token, check_revoked=False)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        logger.info(f"Token verified for user: {email}, uid: {uid}")
        return {
            "firebase_uid": uid,
            "email": email,
            "name": decoded_token.get('name', '')
        }
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        # 오류 메시지를 더 자세히 포함
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"인증 토큰이 유효하지 않습니다: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    token_data: dict = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    try:
        # 토큰 데이터 확인
        logger.info(f"Token data: {token_data}")
        
        # 데이터베이스에서 사용자 조회
        firebase_uid = token_data["firebase_uid"]
        logger.info(f"Looking for user with firebase_uid: {firebase_uid}")
        
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            logger.error(f"User not found for firebase_uid: {firebase_uid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"firebase_uid '{firebase_uid}'에 해당하는 사용자를 찾을 수 없습니다"
            )
        
        logger.info(f"User found: {user.email}")
        return user
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보를 가져오는 중 오류 발생: {str(e)}"
        ) 