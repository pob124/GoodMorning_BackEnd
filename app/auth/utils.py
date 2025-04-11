from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from app.models.database_models import User
from app.core.firebase import initialize_firebase
from sqlalchemy.orm import Session
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
firebase_app = initialize_firebase()

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # Firebase ID 토큰 검증
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        return {
            "firebase_uid": uid,
            "email": email,
            "name": decoded_token.get('name', '')
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.firebase_uid == token_data["firebase_uid"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    return user 